import base64
import json
import logging
import os
from typing import Any, Optional, Sequence
from urllib import error, request

OPENAI_FAST_MODEL = os.getenv("OPENAI_FAST_MODEL", "gpt-5.4-mini")
OPENAI_PRECISE_MODEL = os.getenv("OPENAI_PRECISE_MODEL", "gpt-5.5")
OPENAI_OCR_MODEL = os.getenv("OPENAI_OCR_MODEL", OPENAI_PRECISE_MODEL)
OPENAI_API_TIMEOUT_SECONDS = int(os.getenv("OPENAI_API_TIMEOUT_SECONDS", "180"))
# 0=ChatGPT同型の1pass（推奨） / 1=OCR分割の2段階（実験）
SPLIT_TWO_STAGE = os.getenv("MARUKE_SPLIT_TWO_STAGE", "0").strip().lower() in {"1", "true", "yes"}

VALID_GRADING_MODES = {"simple", "rich"}

logger = logging.getLogger("maruke.grader")


class GraderError(Exception):
    pass


SYSTEM_PROMPT = """あなたは中学受験生の家庭学習を支える、丁寧で正確な採点者です。
保護者が子どもの宿題（塾・進研・Z会・学校プリント）の丸つけを楽にするためのアプリの一部として動きます。

【最重要ルール】
1. 写真に「解答（正解）」が一緒に写っている場合は、それを最優先で正解の根拠にする（自分で解き直さない）。basis="answer_key"。
2. 解答が写っていない場合のみ、自分で問題を解いて正解を求める。basis="solved"。
3. 自分で解いた結果に少しでも自信がない、または子どもの答えが読み取りにくい場合は、
   勝手に incorrect にせず verdict="uncertain"（要確認）にする。誤採点で保護者を惑わせないことが何より大事。
4. 子どもの答えが書かれていない空欄の設問でも、問題文が読める場合は必ず自分で解いて correct_answer に正答例を書く。
   その場合 child_answer="（未記入）"、verdict="uncertain"、basis="solved" とし、comment には「答えを書くなら〇〇」のように短く示す。
5. 国語の記述・作文など機械採点が不向きな設問でも、問題文が読める場合は正答例や書き方の例を correct_answer に作る。
   ただし採点は verdict="uncertain" にし、comment に観点だけ示す（無理に○×をつけない）。
6. 縦書き（タテ書き）の国語プリントでも、右から左・上から下の順で設問を読み取る。
7. 見開き2ページが1枚の写真に写っている場合は、両ページの設問を読み取る。自信がない設問は uncertain にする。
8. 【見開き2枚モード】左右ページが別々の写真として送られた場合、同一ワークの見開きとして1つの宿題とみなす。
    - 1枚目＝左ページ、2枚目＝右ページ（3枚目以降は続きページ）。順番を入れ替えない。
    - 国語ワークでは問題文・本文・設問と子どもの手書き答え（選択マーク・記述・語句）が同じページにある。
    - 縦書きは各ページ内で右→左・上→下。2ページにまたがる文章は左ページの続きを右ページで読む。
    - 記述・抜き出し・漢字・語句問題は手書きを child_answer に。空欄のみで手書きがなければ未記入。
    - 国語の記述は完全一致でなくても要点が合えば correct、微妙なら uncertain（厳しすぎない）。
9. 選択肢がある問題では、必ず写真に印刷された選択肢の中から答えを選ぶ。選択肢外の答えを勝手に作らない。
10. child_answer には「子どもが鉛筆・ペンで手書きした内容」だけを入れる。問題文に印刷されている選択肢ラベル（ア・イ・ウなど）、番号、見出し、例文は child_answer に入れない。
11. 丸・枠・下線の空欄に手書きがない場合は必ず未記入とする。空欄を推測して「ウ」などと書いたり、graded / correct にしない。
12. result_type="answer_example"（未記入）のときは verdict は必ず uncertain、basis は answer_key にしない（採点していないので解答照合ではない）。
13. 【問題と答案が別画像】問題プリントと答案ノートが分かれている場合:
    - 問題文・図・選択肢は「問題プリント」から読む。空欄□に手書きがなくても、答案ノートに (1)(2)… の答えがあればそこから child_answer を読む。
    - 設問番号 (1)(2)… で問題プリントと答案ノートを対応づける。番号の対応が不明な設問は verdict=uncertain。
    - 答案ノートの途中式と最終答えを区別する。赤丸・二重線・下線で囲った数字が最終答えのことが多い。
    - 問題プリントだけで空欄の設問に、答案ノートに該当番号の手書きがなければ child_answer="（未記入）"、result_type=answer_example。
14. 子どもの手書き数字・分数・単位は画像をよく見て読む。480 と 32、0.08 と 0.18 など似た桁を取り違えない。読み取りに自信がなければ uncertain。
15. 【手書き答案の読み取り】答案ノートでは印刷文字ではなく鉛筆・ペンの筆跡だけを child_answer に書く。
    - 縦書きの筆算・除法は最終行・最下段の数字を最終答えとする。途中の計算行は child_answer に含めない。
    - 小数点の位置を慎重に見る（0.85 と 0.18、314 と 31.4）。点が小さくても推測で動かさない。
    - 帯分数は「3と1/3」「2と4/9」の表記。分子分母の上下関係を画像どおりに読む。
    - 単位（cm・秒・倍・%）が書いてあれば child_answer に含める。
    - 設問番号 (1)(2)… と答案の並びを対応づける。番号が写真に写っていなければ uncertain。
    - 消しゴムで薄くなった字・かすれた鉛筆は推測せず uncertain。
16. 問題文を要約するとき、与えられた数字・記号を落とさない（例: 並べ替え問題では使える数字をすべて使う）。
17. correct_answer と explanation の数値は必ず一致させる。矛盾したら confidence=low、verdict=uncertain。
18. 【算数プリントの読み取り】
    - 除法の筆算（0.4）83.6 など）は「83.6÷0.4」であり掛け算ではない。
    - 「8/15 分」「15分の8分」= 8/15 分（時間）。「8分の15」「15/8 分」と読み替えない。
    - 帯分数は「3と1/3」「4と2/9」の表記を維持。LaTeX は使わずプレーンテキスト。
    - question には印刷された問題文を要約せず書き写す（数字・記号を落とさない）。

【モードの区別（result_type）】
- 子どもの手書きの答えがあり、それと正解を比較した: result_type="graded"
- 答えが未記入で、正解だけを表示する: result_type="answer_example"（verdict は uncertain、採点しない）
- 問題文・図が読めず判定不能: result_type="unreadable"（basis="unknown"）

【採点の基準】
- 数値・式・用語・記号は、表記ゆれ（全角半角、約分の有無、単位の有無など）を考慮して柔軟に正誤判定する。
- 子どもが空欄の設問は child_answer="（未記入）" とし、問題文が読める限り correct_answer にAIが作った正答例を書く。
- correct_answer は、保護者がそのまま見て使える答えだけを簡潔に書く。説明は comment に分ける。
- 問題文そのものが読めない場合だけ、correct_answer="画像確認が必要"、basis="unknown"、verdict="uncertain" とする。
- question は設問の内容を正確に書く。問題プリント＋答案ノート分割時は印刷を書き写し、1枚撮影時は短く要約してよい。
- comment は採点時の短い一言（20文字前後）。正解のお褒め・惜しい点のヒント。
- explanation は「ママ向け解説」。採点する保護者が自分の頭で理解し、子に教えるための手順書。
  専門用語は使うなら平易に補足。3〜5文。「まず〇〇→次に△△→だから答えは××」の流れで書く。
  中学受験に詳しくないママでも採点・指導できることを最優先。
- child_tip は「子ども向けヒント」。子どもが自分で読めるやさしい日本語で1〜2文。
  図や比喩を使って、答えのイメージが湧くように書く。
- diagram_svg は図形・作図・角度・面積・グラフ・座標など視覚が必要な設問だけ、
  子どもが見てわかる補助図を SVG で1つ書く。不要な設問は空文字 ""。
  形式: 単一の <svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">…</svg>
  線・円・多角形・弧・text のみ。script/style/foreignObject は禁止。色は黒線＋薄い塗り。
  角度・辺の長さ・記号（○△）をラベルで示す。
- explanation / child_tip は result_type が answer_example でも graded でも必ず書く（unreadable 時のみ省略可）。

すべて日本語で出力する。"""

SIMPLE_MODE_INSTRUCTION = (
    "【お手軽モード】答えと○×だけを優先。explanation・child_tip・diagram_svg は必ず空文字 \"\"。"
    "comment は採点時のみ20文字以内。未記入は correct_answer に答えだけ。"
)


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subject_detected": {"type": "string"},
        "answer_key_present": {"type": "boolean"},
        "summary": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "string"},
                    "question": {"type": "string"},
                    "child_answer": {"type": "string"},
                    "correct_answer": {"type": "string"},
                    "verdict": {
                        "type": "string",
                        "enum": ["correct", "incorrect", "uncertain"],
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "basis": {
                        "type": "string",
                        "enum": ["answer_key", "solved", "unknown"],
                    },
                    "result_type": {
                        "type": "string",
                        "enum": ["graded", "answer_example", "unreadable"],
                    },
                    "comment": {"type": "string"},
                    "explanation": {"type": "string"},
                    "child_tip": {"type": "string"},
                    "diagram_svg": {"type": "string"},
                },
                "required": [
                    "number",
                    "question",
                    "child_answer",
                    "correct_answer",
                    "verdict",
                    "confidence",
                    "basis",
                    "result_type",
                    "comment",
                    "explanation",
                    "child_tip",
                    "diagram_svg",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subject_detected", "answer_key_present", "summary", "items"],
    "additionalProperties": False,
}

PROBLEM_EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "subject_detected": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "string"},
                    "question": {"type": "string"},
                    "read_confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
                "required": ["number", "question", "read_confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["subject_detected", "items"],
    "additionalProperties": False,
}

PROBLEM_OCR_SYSTEM = """あなたは中学受験プリントの OCR 専門家です。画像に写っている印刷文字だけを正確に書き写します。

【絶対ルール】
1. 要約・言い換え・解釈は禁止。印刷されている文言をそのまま question に写す。
2. 数字・記号・単位・分数・帯分数・小数・選択肢（ア・イ・ウ）は1文字も変えない。
3. 画像に無い問題を作らない。見えない設問は出力しない。
4. 空欄□は「□」のまま残す。空欄に子の手書きがあっても無視（問題プリントには答えは通常ない）。
5. 2段組・2列レイアウトは左列の上から下、次に右列の上から下の順で (1)(2)… を付ける。
6. 縦書き国語は右→左、上→下。算数の筆算・除法の縦書き形式もそのまま写す。
7. 長文は省略しない。1設問 = items の1要素。
8. 読み取りに自信がなければ read_confidence=low。推測で埋めない。

Output JSON only."""

ANSWER_OCR_SYSTEM = """あなたは答案ノートの手書き読み取り専門家です。鉛筆・ペンの筆跡だけを child_answer に写します。

【絶対ルール】
1. 印刷文字・問題文・設問文は無視。手書きの答えだけを読む。
2. 赤丸・赤ペン・二重線・下線で囲った数字・式が最終答え。これを最優先で child_answer に写す。
3. 途中式・筆算の各行は child_answer に含めない（最終答えのみ）。
4. 除法の筆算: 商の各桁を上から順に並べた数が答え（商が 2 と 9 なら 209）。小数点が明確に見える場合のみ "." を入れる（209 と 20.9 を取り違えない）。
5. 480と32、0.85と0.18、314と31.4、209と20 のような桁・小数点の取り違えに注意。
6. 帯分数は「2と4/9」形式。単位（秒・cm・倍・%）が手書きされていれば含める。
7. 設問番号 (1)(2)… と答案の位置を対応づける。番号が写っていなければ read_confidence=low。
8. 消えかけ・薄い字・かすれた鉛筆は推測で埋めない。read_confidence=low。
9. 手書きがなければ child_answer="（未記入）"。

Output JSON only."""

ANSWER_EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "string"},
                    "child_answer": {"type": "string"},
                    "read_confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                },
                "required": ["number", "child_answer", "read_confidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["items"],
    "additionalProperties": False,
}


def _grade_profile(grade_level: Optional[str], grading_mode: str = "rich") -> dict[str, Any]:
    grade = (grade_level or "").strip()
    if grade in {"1", "2"}:
        profile = {
            "model": OPENAI_FAST_MODEL,
            "image_detail": "high",
            "max_output_tokens": 6000,
            "label": f"小学{grade}年・高速",
        }
    elif grade in {"3", "4"}:
        profile = {
            "model": OPENAI_FAST_MODEL,
            "image_detail": "high",
            "max_output_tokens": 8000,
            "label": f"小学{grade}年・標準",
        }
    elif grade in {"5", "6"}:
        profile = {
            "model": OPENAI_PRECISE_MODEL,
            "image_detail": "high",
            "max_output_tokens": 14000,
            "label": f"小学{grade}年・精密",
        }
    else:
        profile = {
            "model": OPENAI_FAST_MODEL,
            "image_detail": "high",
            "max_output_tokens": 8000,
            "label": "学年おまかせ・標準",
        }

    if grading_mode == "simple":
        profile = dict(profile)
        profile["model"] = OPENAI_FAST_MODEL
        profile["image_detail"] = "low"
        profile["max_output_tokens"] = min(profile["max_output_tokens"], 3500)
        profile["label"] = profile["label"] + "・お手軽"
    else:
        profile = dict(profile)
        profile["label"] = profile["label"] + "・解説リッチ"

    return profile


def _image_part(image_bytes: bytes, media_type: str, image_detail: str) -> dict[str, Any]:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{media_type};base64,{b64}",
            "detail": image_detail,
        },
    }


def _is_unfilled_answer(child: str) -> bool:
    s = (child or "").strip()
    if not s:
        return True
    if "未記入" in s or s in {"（空欄）", "空欄", "—", "－", "-"}:
        return True
    return False


def _infer_result_type(item: dict[str, Any]) -> str:
    explicit = item.get("result_type")
    basis = item.get("basis", "")
    child = item.get("child_answer", "")
    correct = item.get("correct_answer", "")
    if basis == "unknown" or "画像確認" in correct:
        return "unreadable"
    if _is_unfilled_answer(child):
        return "answer_example"
    if explicit in {"graded", "answer_example", "unreadable"}:
        return explicit
    return "graded"


def _sanitize_svg(svg: str) -> str:
    s = (svg or "").strip()
    if not s or not s.lower().startswith("<svg"):
        return ""
    blocked = ("<script", "javascript:", "onload", "onclick", "foreignobject", "<style")
    lower = s.lower()
    if any(b in lower for b in blocked):
        return ""
    return s


def _normalize_item(item: dict[str, Any], grading_mode: str = "rich") -> dict[str, Any]:
    item["result_type"] = _infer_result_type(item)
    item["diagram_svg"] = _sanitize_svg(item.get("diagram_svg", ""))

    if item["result_type"] == "answer_example":
        item["child_answer"] = "（未記入）"
        item["verdict"] = "uncertain"
        if item.get("basis") == "answer_key":
            item["basis"] = "solved"
        if grading_mode == "rich":
            if not (item.get("explanation") or "").strip():
                correct = (item.get("correct_answer") or "").strip()
                if correct and "画像確認" not in correct:
                    item["explanation"] = f"正解は{correct}です。"

    if grading_mode == "simple":
        item["explanation"] = ""
        item["child_tip"] = ""
        item["diagram_svg"] = ""

    if item["result_type"] == "unreadable":
        item["verdict"] = "uncertain"
        item["basis"] = "unknown"

    return item


def _normalize_items(
    items: list[dict[str, Any]],
    answer_key_present: bool = False,
    grading_mode: str = "rich",
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not answer_key_present and item.get("basis") == "answer_key":
            item["basis"] = "solved"
            item["child_answer"] = "（未記入）"
        normalized.append(_normalize_item(item, grading_mode))
    return normalized


def _with_counts(data: dict[str, Any], grading_mode: str = "rich") -> dict[str, Any]:
    answer_key_present = bool(data.get("answer_key_present"))
    items = _normalize_items(data.get("items", []), answer_key_present, grading_mode)
    data["items"] = items
    data["total"] = len(items)
    graded = [item for item in items if item.get("result_type") == "graded"]
    data["graded_count"] = len(graded)
    data["answer_example_count"] = sum(
        1 for item in items if item.get("result_type") == "answer_example"
    )
    data["unreadable_count"] = sum(1 for item in items if item.get("result_type") == "unreadable")
    data["correct_count"] = sum(1 for item in graded if item.get("verdict") == "correct")
    data["incorrect_count"] = sum(1 for item in graded if item.get("verdict") == "incorrect")
    data["uncertain_count"] = sum(1 for item in graded if item.get("verdict") == "uncertain")
    if data["graded_count"] == 0 and data["answer_example_count"] > 0:
        if grading_mode == "simple":
            data["summary"] = (
                f"答案は未記入でした。{data['answer_example_count']}問の答えを表示しています。"
            )
        else:
            data["summary"] = (
                f"答案は未記入でした。{data['answer_example_count']}問の答えと解説を表示しています。"
            )
    data["grading_mode"] = grading_mode
    return data


def _post_chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise GraderError("OPENAI_API_KEY が未設定です。")

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=OPENAI_API_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise GraderError(f"OpenAI API エラー ({exc.code}): {message}") from exc
    except error.URLError as exc:
        raise GraderError(f"OpenAI API に接続できませんでした: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GraderError(
            "OpenAI API の応答がタイムアウトしました。画像枚数を減らすか、少し時間を置いて再試行してください。"
        ) from exc


def _loads_json_object(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(content[start : end + 1])


def _chat_json_schema(
    *,
    model: str,
    system: str,
    user_content: list[dict[str, Any]] | str,
    schema: dict[str, Any],
    schema_name: str,
    max_tokens: int,
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    if isinstance(user_content, str):
        messages.append({"role": "user", "content": user_content})
    else:
        messages.append({"role": "user", "content": user_content})

    resp = _post_chat_completion(
        {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
            "max_completion_tokens": max_tokens,
        }
    )
    choice = resp.get("choices", [{}])[0]
    if choice.get("finish_reason") == "length":
        raise GraderError("AIの返答が途中で切れました。写真枚数を減らして再試行してください。")
    content = choice.get("message", {}).get("content")
    if not content:
        raise GraderError("OpenAI API から空の結果が返りました。")
    try:
        return _loads_json_object(content)
    except json.JSONDecodeError as exc:
        raise GraderError("OpenAI API の結果を JSON として読めませんでした。") from exc


def _images_user_content(
    intro: str,
    images: Sequence[tuple[bytes, str]],
    *,
    label: str,
    image_detail: str,
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": intro}]
    for index, (image_bytes, media_type) in enumerate(images, start=1):
        content.extend(
            [
                {"type": "text", "text": f"{label} {index} / {len(images)}"},
                _image_part(image_bytes, media_type, image_detail),
            ]
        )
    return content


def _extract_problems(
    problem_images: Sequence[tuple[bytes, str]],
    profile: dict[str, Any],
    subject_hint: Optional[str],
    grade_level: Optional[str],
) -> dict[str, Any]:
    intro = (
        "【問題プリント OCR】"
        " (1)(2)… の設問番号ごとに、印刷された問題文を verbatim（そのまま）で question に書く。"
        " 見開き・2列でも全設問を漏らさない。"
        " 採点・解答・要約はしない。"
    )
    if subject_hint:
        intro = f"教科: {subject_hint}。" + intro
    if grade_level:
        intro = f"小学{grade_level}年。" + intro
    content = _images_user_content(
        intro,
        problem_images,
        label="【問題プリント】",
        image_detail="high",
    )
    ocr_model = OPENAI_OCR_MODEL
    first = _chat_json_schema(
        model=ocr_model,
        system=PROBLEM_OCR_SYSTEM,
        user_content=content,
        schema=PROBLEM_EXTRACT_SCHEMA,
        schema_name="problem_extract",
        max_tokens=8000,
    )
    verify_intro = (
        "前回の OCR 結果を画像と照合し、誤字・脱落・要約ミスを修正した完全版を返す。"
        " 数字や記号の取り違えがあれば必ず直す。画像に無い設問は削除。"
        f"\n\n【前回 OCR】\n{json.dumps(first, ensure_ascii=False)}"
    )
    verify_content = _images_user_content(
        verify_intro,
        problem_images,
        label="【問題プリント・再確認】",
        image_detail="high",
    )
    verified = _chat_json_schema(
        model=ocr_model,
        system=PROBLEM_OCR_SYSTEM,
        user_content=verify_content,
        schema=PROBLEM_EXTRACT_SCHEMA,
        schema_name="problem_extract_verify",
        max_tokens=8000,
    )
    logger.info(
        "problem OCR model=%s pass1=%d pass2=%d items",
        ocr_model,
        len(first.get("items", [])),
        len(verified.get("items", [])),
    )
    return verified


def _extract_answers(
    answer_images: Sequence[tuple[bytes, str]],
    profile: dict[str, Any],
    grade_level: Optional[str],
) -> dict[str, Any]:
    intro = (
        "答案ノートから子どもの手書き答えだけを読み取る。問題文は書かない。"
        "各マス・各設問の (1)(2)… 番号に対応づけ、最終答えを child_answer に書く。"
        "赤丸・下線・二重線で囲った数字を最終答えとして最優先。途中式は無視。"
        "手書きがなければ child_answer=\"（未記入）\"。"
        "480と32、0.84と0.08、209と20.9 のような桁・小数点を取り違えない。"
        "自信がなければ read_confidence=low。"
    )
    if grade_level:
        intro = f"小学{grade_level}年の答案。" + intro
    content = _images_user_content(
        intro,
        answer_images,
        label="【答案ノート】",
        image_detail="high",
    )
    ocr_model = OPENAI_OCR_MODEL
    return _chat_json_schema(
        model=ocr_model,
        system=ANSWER_OCR_SYSTEM,
        user_content=content,
        schema=ANSWER_EXTRACT_SCHEMA,
        schema_name="answer_extract",
        max_tokens=4000,
    )


def _grade_from_extracts(
    *,
    problems: dict[str, Any],
    answers: dict[str, Any],
    profile: dict[str, Any],
    mode: str,
    grade_level: Optional[str],
    subject_hint: Optional[str],
    key_image: Optional[bytes],
    key_media_type: Optional[str],
) -> dict[str, Any]:
    payload = {
        "problems": problems.get("items", []),
        "answers": answers.get("items", []),
    }
    intro = (
        "以下は問題プリントと答案ノートから OCR した JSON です。"
        "設問番号で対応づけ、採点結果 JSON を出力する。"
        "answers の read_confidence=low の設問は verdict=uncertain を優先。"
        "problems の read_confidence=low の設問も verdict=uncertain を優先。"
        "question フィールドは problems の question をそのまま使う（短く書き換えない）。"
        "child_answer は answers の値をそのまま使う（書き換えない）。"
        f"\n\n{json.dumps(payload, ensure_ascii=False)}"
    )
    if mode == "simple":
        intro += SIMPLE_MODE_INSTRUCTION

    user_content: list[dict[str, Any]] = [{"type": "text", "text": intro}]
    if key_image is not None:
        user_content.extend(
            [
                {
                    "type": "text",
                    "text": "次の画像は公式解答ページ。正解はここを最優先（basis=answer_key）。",
                },
                _image_part(key_image, key_media_type or "image/jpeg", profile["image_detail"]),
            ]
        )

    closing = "設問ごとに採点してください。"
    if grade_level:
        closing = f"対象は小学{grade_level}年生です。" + closing
    if subject_hint:
        closing = f"教科は「{subject_hint}」です。" + closing
    user_content.append({"type": "text", "text": closing})

    data = _chat_json_schema(
        model=profile["model"],
        system=SYSTEM_PROMPT,
        user_content=user_content,
        schema=OUTPUT_SCHEMA,
        schema_name="grading",
        max_tokens=profile["max_output_tokens"],
    )
    data["answer_key_present"] = key_image is not None
    if not data.get("subject_detected"):
        data["subject_detected"] = problems.get("subject_detected") or subject_hint or ""
    return data


def _grade_split_two_stage(
    *,
    normalized_problem_images: Sequence[tuple[bytes, str]],
    normalized_answer_images: Sequence[tuple[bytes, str]],
    profile: dict[str, Any],
    mode: str,
    grade_level: Optional[str],
    subject_hint: Optional[str],
    key_image: Optional[bytes],
    key_media_type: Optional[str],
) -> dict[str, Any]:
    logger.info(
        "split two-stage start model=%s problems=%d answers=%d",
        profile["model"],
        len(normalized_problem_images),
        len(normalized_answer_images),
    )
    problems = _extract_problems(
        normalized_problem_images, profile, subject_hint, grade_level
    )
    answers = _extract_answers(normalized_answer_images, profile, grade_level)
    logger.info(
        "split extract done problems=%d answers=%d",
        len(problems.get("items", [])),
        len(answers.get("items", [])),
    )
    if os.getenv("MARUKE_DEBUG_EXTRACT") == "1":
        logger.info("extract problems=%s", json.dumps(problems, ensure_ascii=False)[:2000])
        logger.info("extract answers=%s", json.dumps(answers, ensure_ascii=False)[:2000])

    data = _grade_from_extracts(
        problems=problems,
        answers=answers,
        profile=profile,
        mode=mode,
        grade_level=grade_level,
        subject_hint=subject_hint,
        key_image=key_image,
        key_media_type=key_media_type,
    )
    data["grading_strategy"] = "split_two_stage"
    data["grading_profile"] = profile["label"] + "・2段階"
    data["layout_mode"] = "split"
    result = _with_counts(data, mode)
    if os.getenv("MARUKE_INCLUDE_OCR_PREVIEW", "1").strip().lower() not in {"0", "false", "no"}:
        result["ocr_preview"] = {
            "problems": problems.get("items", []),
            "answers": answers.get("items", []),
        }
    logger.info(
        "grade done strategy=split_two_stage items=%d correct=%d incorrect=%d uncertain=%d",
        result.get("total", 0),
        result.get("correct_count", 0),
        result.get("incorrect_count", 0),
        result.get("uncertain_count", 0),
    )
    return result


def demo_result(
    subject_hint: Optional[str] = None,
    grade_level: Optional[str] = None,
    grading_mode: str = "rich",
) -> dict[str, Any]:
    profile = _grade_profile(grade_level, grading_mode)
    data = {
        "demo": True,
        "subject_detected": subject_hint or "算数",
        "answer_key_present": False,
        "summary": f"デモ結果です（APIキー未設定）。採点設定: {profile['label']}。",
        "grading_profile": profile["label"],
        "items": [
                {
                    "number": "1",
                    "question": "12 + 8",
                    "child_answer": "20",
                    "correct_answer": "20",
                    "verdict": "correct",
                    "confidence": "high",
                    "basis": "solved",
                    "result_type": "graded",
                    "comment": "正しく計算できています。",
                    "explanation": "まず12と8を足す問題です。10と8を足して18、残りの2を足して20になります。",
                    "child_tip": "10と8を足してから、あと2を足すと楽だよ。",
                    "diagram_svg": "",
                },
                {
                    "number": "2",
                    "question": "つるとかめが合わせて8匹、足が22本。つるは何羽？",
                    "child_answer": "5羽",
                    "correct_answer": "つる5羽、かめ3匹",
                    "verdict": "incorrect",
                    "confidence": "medium",
                    "basis": "solved",
                    "result_type": "graded",
                    "comment": "つるだけ答えて惜しい！かめも数えよう。",
                    "explanation": "頭が8匹・足が22本の条件を満たす組を探します。つる5・かめ3なら頭8・足22でピッタリ。つるだけ5と答えるとかめの数が抜けます。",
                    "child_tip": "つるは2本足、かめは4本足。足の合計から考えよう。",
                    "diagram_svg": "",
                },
                {
                    "number": "3",
                    "question": "図形の角度問題",
                    "child_answer": "（未記入）",
                    "correct_answer": "60°",
                    "verdict": "uncertain",
                    "confidence": "low",
                    "basis": "solved",
                    "result_type": "answer_example",
                    "comment": "図を一緒に見てみましょう。",
                    "explanation": "三角形は3つの角を足すと必ず180°になります。図で分かっている2つの角を足し、180°から引けば残りの角が出ます。",
                    "child_tip": "三角形の角は、3つ合わせて180度になるよ。",
                    "diagram_svg": (
                        '<svg viewBox="0 0 240 240" xmlns="http://www.w3.org/2000/svg">'
                        '<polygon points="40,200 200,200 120,40" fill="#eff6ff" stroke="#1f2937" stroke-width="2"/>'
                        '<text x="115" y="215" font-size="14" fill="#1f2937">底辺</text>'
                        '<text x="30" y="130" font-size="14" fill="#dc2626">60°</text>'
                        '<text x="175" y="130" font-size="14" fill="#1f2937">?</text>'
                        '</svg>'
                    ),
                },
            ],
    }
    return _with_counts(data, grading_mode)


def _spread_page_label(index: int, total: int) -> str:
    if total == 2:
        return "左ページ" if index == 1 else "右ページ"
    if index == 1:
        return "1ページ目（左）"
    if index == 2:
        return "2ページ目（右）"
    return f"続き {index}ページ目"


def _build_user_content(
    *,
    profile: dict[str, Any],
    mode: str,
    normalized_answer_images: Sequence[tuple[bytes, str]],
    normalized_problem_images: Sequence[tuple[bytes, str]],
    key_image: Optional[bytes],
    key_media_type: Optional[str],
    grade_level: Optional[str],
    subject_hint: Optional[str],
    layout_mode: str = "combined",
    answer_hints: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    split_mode = bool(normalized_problem_images)
    spread_mode = layout_mode == "spread" and not split_mode
    if split_mode:
        intro = (
            "【1枚目＝問題プリント、2枚目以降＝答案ノート】"
            " ChatGPT に「1枚目は問題、2枚目は回答、答え合わせして」と依頼するのと同じ作業です。"
            " 問題プリントと答案ノートを見比べ、(1)(2)… ごとに採点してください。"
            " 問題文は印刷をそのまま question に写す（×と÷を入れ替えない）。"
            " 空欄□だけ見て未記入と決めない。答案ノートに (1) の手書きがあれば採点する。"
            " 答案ノートの赤丸・最終行の数字を child_answer にする（途中式は含めない）。"
            " 手書きは鉛筆の筆跡を拡大して読む。小数点・分数の上下・単位を落とさない。"
            " 480と32、0.85と0.18、314と31.4、209と20.9 のような桁取り違えに注意。"
            " 読み取りに自信がなければ verdict=uncertain（誤採点より要確認を優先）。"
        )
        if answer_hints and answer_hints.get("items"):
            intro += (
                "\n\n【答案ノート事前読み取り（画像で必ず照合。矛盾があれば画像を優先し read_confidence=low は uncertain）】\n"
                + json.dumps(answer_hints.get("items", []), ensure_ascii=False)
            )
    elif spread_mode:
        intro = (
            "【見開き2枚モード — 国語・理科などワーク向け】"
            " 複数枚の写真は同一見開きの左右ページです（1枚目＝左、2枚目＝右、以降は続き）。"
            " 1つの宿題として両ページを合わせて読み、すべての設問を漏らさず採点してください。"
            " 各ページには印刷された問題文・本文・設問と、子どもの鉛筆・ペンの手書き答えが一緒に写っています。"
            " 国語の縦書きは各ページ内で右→左・上→下。2ページにまたがる文章は左→右の順に繋げて読む。"
            " 選択マーク（ア・イ・ウの丸付け）、漢字・語句の記入、記述文を child_answer に書く。"
            " 記述問題は要点が合えば correct、表現の違いだけなら柔軟に。自信がなければ uncertain。"
            " 印刷文字を child_answer に入れない。空欄に手書きがなければ未記入。"
        )
    else:
        intro = (
            "次の画像は、子どもが解いた宿題（問題と子どもの答え）です。"
            "複数枚ある場合は同じ宿題の続きとして、画像の順番に設問を読み取ってください。"
            "各設問について、鉛筆・ペンで手書きされた答えが写真に見える場合のみ mode=採点（result_type=graded）で答え合わせする。"
            "空欄・未記入の場合は mode=答え表示（result_type=answer_example）とし、"
            "child_answer は必ず「（未記入）」、correct_answer に正解を書く（採点しない）。"
        )
    if mode == "simple":
        intro += SIMPLE_MODE_INSTRUCTION
    else:
        intro += (
            "explanation（ママ向け）・child_tip（子ども向け）・必要なら diagram_svg も書く。"
        )
    intro += (
        "印刷されている選択肢ラベル（ア・イ・ウなど）を子どもの答えと誤認しない。"
        "問題が読めない場合のみ result_type=unreadable とする。"
    )

    user_content: list[dict[str, Any]] = [{"type": "text", "text": intro}]

    if split_mode:
        for index, (image_bytes, media_type) in enumerate(normalized_problem_images, start=1):
            user_content.extend(
                [
                    {
                        "type": "text",
                        "text": f"【問題プリント】{index} / {len(normalized_problem_images)}（問題文・空欄・図。手書き答えはここではなく答案ノートを見る）",
                    },
                    _image_part(image_bytes, media_type, profile["image_detail"]),
                ]
            )
        for index, (image_bytes, media_type) in enumerate(normalized_answer_images, start=1):
            user_content.extend(
                [
                    {
                        "type": "text",
                        "text": f"【答案ノート】{index} / {len(normalized_answer_images)}（(1)(2)… の手書き答え・途中式。最終答えを child_answer に）",
                    },
                    _image_part(image_bytes, media_type, profile["image_detail"]),
                ]
            )
    else:
        total = len(normalized_answer_images)
        for index, (image_bytes, media_type) in enumerate(normalized_answer_images, start=1):
            if spread_mode:
                page = _spread_page_label(index, total)
                caption = (
                    f"【見開き {page}】{index} / {total}"
                    "（問題文＋手書き答案。左→右の順で同一宿題として読む）"
                )
            else:
                caption = f"答案写真 {index} / {total}"
            user_content.extend(
                [
                    {"type": "text", "text": caption},
                    _image_part(image_bytes, media_type, profile["image_detail"]),
                ]
            )

    if key_image is not None:
        user_content.extend(
            [
                {
                    "type": "text",
                    "text": "次の画像は、上の問題に対応する解答（正解）です。これを正解の根拠として優先してください。",
                },
                _image_part(key_image, key_media_type or "image/jpeg", profile["image_detail"]),
            ]
        )

    closing = "設問ごとに採点してください。"
    if grade_level:
        closing = f"対象は小学{grade_level}年生です。学年相応の考え方で採点してください。" + closing
    if subject_hint:
        closing = f"この宿題の教科は「{subject_hint}」です。" + closing
    user_content.append({"type": "text", "text": closing})
    return user_content


def grade(
    answer_image: Optional[bytes] = None,
    answer_media_type: str = "image/jpeg",
    subject_hint: Optional[str] = None,
    grade_level: Optional[str] = None,
    key_image: Optional[bytes] = None,
    key_media_type: Optional[str] = None,
    answer_images: Optional[Sequence[tuple[bytes, str]]] = None,
    problem_images: Optional[Sequence[tuple[bytes, str]]] = None,
    grading_mode: str = "rich",
    layout_mode: str = "combined",
) -> dict[str, Any]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise GraderError("OPENAI_API_KEY が未設定です。")

    mode = grading_mode if grading_mode in VALID_GRADING_MODES else "rich"
    profile = _grade_profile(grade_level, mode)
    normalized_answer_images = list(answer_images or [])
    if not normalized_answer_images and answer_image is not None:
        normalized_answer_images = [(answer_image, answer_media_type)]
    normalized_problem_images = list(problem_images or [])
    if not normalized_answer_images:
        raise GraderError("採点する答案写真がありません。")
    if normalized_problem_images and not normalized_answer_images:
        raise GraderError("答案ノートの写真を1枚以上選んでください。")

    layout = (layout_mode or "combined").strip()
    if layout not in {"combined", "split", "spread"}:
        layout = "combined"

    if normalized_problem_images and SPLIT_TWO_STAGE:
        return _grade_split_two_stage(
            normalized_problem_images=normalized_problem_images,
            normalized_answer_images=normalized_answer_images,
            profile=profile,
            mode=mode,
            grade_level=grade_level,
            subject_hint=subject_hint,
            key_image=key_image,
            key_media_type=key_media_type,
        )

    # 分割・見開き2枚は精密モデル + 高解像度固定
    answer_hints: Optional[dict[str, Any]] = None
    if normalized_problem_images or layout == "spread":
        profile = dict(profile)
        profile["model"] = OPENAI_PRECISE_MODEL
        profile["image_detail"] = "high"
        suffix = "・分割1pass" if normalized_problem_images else "・見開き2枚"
        profile["label"] = profile.get("label", "") + suffix

    if normalized_problem_images and not SPLIT_TWO_STAGE:
        logger.info("split answer prefetch start answers=%d", len(normalized_answer_images))
        answer_hints = _extract_answers(normalized_answer_images, profile, grade_level)
        logger.info(
            "split answer prefetch done items=%d",
            len(answer_hints.get("items", [])),
        )

    user_content = _build_user_content(
        profile=profile,
        mode=mode,
        normalized_answer_images=normalized_answer_images,
        normalized_problem_images=normalized_problem_images,
        key_image=key_image,
        key_media_type=key_media_type,
        grade_level=grade_level,
        subject_hint=subject_hint,
        layout_mode=layout,
        answer_hints=answer_hints,
    )

    resp = _post_chat_completion(
        {
            "model": profile["model"],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "grading",
                    "schema": OUTPUT_SCHEMA,
                    "strict": True,
                },
            },
            "max_completion_tokens": profile["max_output_tokens"],
        }
    )

    choice = resp.get("choices", [{}])[0]
    if choice.get("finish_reason") == "length":
        raise GraderError(
            "問題数が多く、AIの返答が途中で切れました。写真を1ページずつ、または範囲を絞って撮り直してください。"
        )

    content = choice.get("message", {}).get("content")
    if not content:
        raise GraderError("OpenAI API から空の結果が返りました。")

    try:
        data = _loads_json_object(content)
    except json.JSONDecodeError as exc:
        raise GraderError("OpenAI API の結果を JSON として読めませんでした。") from exc

    data["answer_key_present"] = key_image is not None
    data["grading_profile"] = profile["label"]
    if normalized_problem_images:
        data["layout_mode"] = "split"
        data["grading_strategy"] = (
            "split_unified_prefetch" if answer_hints is not None else "split_unified"
        )
    elif layout == "spread":
        data["layout_mode"] = "spread"
        data["grading_strategy"] = "spread_unified"
    else:
        data["layout_mode"] = "combined"
        data["grading_strategy"] = "single_pass"
    result = _with_counts(data, mode)
    if answer_hints is not None and os.getenv("MARUKE_INCLUDE_OCR_PREVIEW", "1").strip().lower() not in {
        "0",
        "false",
        "no",
    }:
        result["ocr_preview"] = {"answers": answer_hints.get("items", [])}
    logger.info(
        "grade done strategy=%s layout=%s items=%d correct=%d incorrect=%d",
        data["grading_strategy"],
        data["layout_mode"],
        result.get("total", 0),
        result.get("correct_count", 0),
        result.get("incorrect_count", 0),
    )
    return result
