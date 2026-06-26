#!/usr/bin/env python3
"""DeepSeek API のまるつけ適合性を小さく検証する。

1. Vision: 答案画像をそのまま送れるか（公式 API は 2026-06 時点テキストのみの可能性）
2. Text: 問題文＋子の答えテキストだけで採点 JSON が返るか（ハイブリッド構成の PoC）

使い方:
  DEEPSEEK_API_KEY=sk-... python3 tools/maruke_app/run_deepseek_probe.py
  # または apps/maruke-app/.env に DEEPSEEK_API_KEY を追加
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "apps/maruke-app"
REPORTS = APP_DIR / "tests/reports"
FIXTURES = APP_DIR / "tests/fixtures/synthetic"

DEEPSEEK_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

# generate_test_fixtures.py と同内容（OCR なし text-only テスト用）
TEXT_CASES = [
    {
        "id": "juku_math",
        "label": "大手塾風・算数",
        "grade_level": "5",
        "lines": [
            "1. つるとかめが合わせて10匹、足の合計は28本。つるは何羽？",
            "2. 正しいものをア〜ウから選べ。ア 12÷3=4  イ 12÷3=36  ウ 12÷3=6",
            "3. 正方形の1辺が6cm。周の長さは？",
        ],
        "child": ["1. 6羽", "2. ア", "3. 24cm"],
        "expected_verdicts": ["correct", "incorrect", "correct"],
    },
    {
        "id": "shinken_zkai",
        "label": "進研/Z会風",
        "grade_level": "4",
        "lines": [
            "1. 次の数を読み方どおりに書きなさい。四千三百二十",
            "2. 次の数を数字で書きなさい。六万五千",
            "3. 748 + 256 =",
        ],
        "child": ["1. 4320", "2. 65000", "3. 1004"],
        "expected_verdicts": ["correct", "correct", "correct"],
    },
    {
        "id": "kokugo",
        "label": "国語・選択/記述",
        "grade_level": "5",
        "lines": [
            "1. 次の文の空欄に入る言葉をア〜ウから選べ。",
            "   雨が（　）と降っている。 ア ざあざあ  イ ごろごろ  ウ ぴちぴち",
            "2. 次の文を40字以内で説明しなさい。",
            "   なぜ暗くすると眠くなるのか。",
        ],
        "child": ["1. ア", "2. （未記入）"],
        "expected_verdicts": ["correct", "uncertain"],
    },
]

VISION_IMAGE = FIXTURES / "01_juku_math_sapix_style.png"


def _api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "DEEPSEEK_API_KEY 未設定です。\n"
            "  1. https://platform.deepseek.com でキー発行（新規は無料枠あり）\n"
            "  2. apps/maruke-app/.env に DEEPSEEK_API_KEY=sk-... を追加\n"
            "  3. 再実行: python3 tools/maruke_app/run_deepseek_probe.py"
        )
    return key


def _post(payload: dict) -> tuple[int, dict | str]:
    req = urllib.request.Request(
        f"{DEEPSEEK_BASE.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, body


def probe_vision() -> dict:
    if not VISION_IMAGE.exists():
        return {"status": "skipped", "reason": f"画像なし: {VISION_IMAGE}"}

    b64 = base64.standard_b64encode(VISION_IMAGE.read_bytes()).decode("utf-8")
    payload = {
        "model": DEEPSEEK_MODEL,
        "thinking": {"type": "disabled"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この宿題の答案を読んで、設問1の子どもの答えだけ教えて。"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 200,
    }
    start = time.perf_counter()
    code, body = _post(payload)
    elapsed = round(time.perf_counter() - start, 2)
    ok = 200 <= code < 300
    content = ""
    if ok and isinstance(body, dict):
        content = (body.get("choices", [{}])[0].get("message", {}).get("content") or "")[:500]
    return {
        "status": "ok" if ok else "error",
        "http_code": code,
        "elapsed_sec": elapsed,
        "response_preview": content,
        "error": None if ok else body,
    }


def _text_grading_prompt(case: dict) -> str:
    problems = "\n".join(case["lines"])
    answers = "\n".join(case["child"])
    return f"""以下は中学受験家庭の宿題です。JSONだけで採点結果を返してください。

【問題】
{problems}

【子どもの答え】
{answers}

対象学年: 小学{case['grade_level']}年

出力JSON形式:
{{
  "items": [
    {{
      "number": "1",
      "question": "設問要約",
      "child_answer": "子の答え",
      "correct_answer": "正解",
      "verdict": "correct|incorrect|uncertain",
      "result_type": "graded|answer_example|unreadable"
    }}
  ]
}}
未記入は result_type=answer_example, verdict=uncertain にしてください。"""


def probe_text_case(case: dict) -> dict:
    payload = {
        "model": DEEPSEEK_MODEL,
        "thinking": {"type": "disabled"},
        "messages": [
            {
                "role": "system",
                "content": "You are a grading assistant. Output valid json only.",
            },
            {"role": "user", "content": _text_grading_prompt(case)},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }
    start = time.perf_counter()
    code, body = _post(payload)
    elapsed = round(time.perf_counter() - start, 2)
    result = {
        "case_id": case["id"],
        "label": case["label"],
        "status": "error",
        "http_code": code,
        "elapsed_sec": elapsed,
    }
    if not (200 <= code < 300) or not isinstance(body, dict):
        result["error"] = body
        return result

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = body.get("usage", {})
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        result["error"] = f"JSON parse error: {exc}; content={content[:300]}"
        return result

    items = data.get("items", [])
    verdicts = [it.get("verdict") for it in items]
    expected = case["expected_verdicts"]
    matches = [
        v == e for v, e in zip(verdicts, expected, strict=False)
    ]
    result.update(
        {
            "status": "ok",
            "items": items,
            "verdicts": verdicts,
            "expected_verdicts": expected,
            "verdict_match_count": sum(matches),
            "verdict_match_total": len(expected),
            "usage": usage,
        }
    )
    return result


def main() -> None:
    load_dotenv(APP_DIR / ".env")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "generated_at": stamp,
        "provider": "deepseek",
        "model": DEEPSEEK_MODEL,
        "base_url": DEEPSEEK_BASE,
        "vision_probe": probe_vision(),
        "text_cases": [probe_text_case(c) for c in TEXT_CASES],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"deepseek-probe-{stamp}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Report: {out}")
    v = report["vision_probe"]
    print(f"  [vision] {v['status']} HTTP {v.get('http_code')} ({v.get('elapsed_sec')}s)")
    if v.get("error"):
        err = v["error"]
        if isinstance(err, dict):
            print(f"    error: {err.get('error', err)}")
        else:
            print(f"    error: {str(err)[:200]}")
    elif v.get("response_preview"):
        print(f"    preview: {v['response_preview'][:120]}")

    for c in report["text_cases"]:
        if c["status"] == "ok":
            m = c["verdict_match_count"]
            t = c["verdict_match_total"]
            print(
                f"  [text:{c['case_id']}] ok {c['elapsed_sec']}s "
                f"verdicts={c['verdicts']} match={m}/{t} "
                f"tokens={c.get('usage', {}).get('total_tokens', '?')}"
            )
        else:
            print(f"  [text:{c['case_id']}] error: {c.get('error')}")


if __name__ == "__main__":
    main()
