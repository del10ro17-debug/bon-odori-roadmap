# 参加可否の自動共有

**やりたいこと**: 誰かが「回答を保存」→ 全員のウェブページに反映。  
**JSONエクスポートは不要**（バックアップ用に残しています）。

## いちばん簡単な方法（推奨・GAS不要）

リポジトリ直下の **`open_bon_odori_sync_setup.command`** をダブルクリック（1回だけ）。

1. GitHub にログインするよう求められたらブラウザで許可
2. `data.js` に書き込み権限が設定される
3. 表示どおり `git add` → `commit` → `push`

### 手動でやる場合

```bash
brew install gh   # 未インストールなら
gh auth login
chmod +x tools/bon_odori_attendance/setup-github-sync.sh
./tools/bon_odori_attendance/setup-github-sync.sh
git add docs/bon-odori/data.js && git commit -m "Enable attendance auto-sync" && git push
```

### 動き方

| 操作 | 結果 |
|------|------|
| 誰かが「回答を保存」 | GitHub 上の `attendance.json` を更新 |
| 全員の画面 | 約30秒ごとに自動取得（保存直後は自分の画面に即反映） |
| 反映まで | GitHub の更新後、通常 **10〜60秒**（Pages のキャッシュ） |

### 注意

- 設定用トークンは `data.js` に入ります（公開リポジトリ上は見えます）。**bon-odori-roadmap だけ**書き込みできる PAT を使ってください。
- 読み取りは誰でも可能（公開ページのため）。

---

## 別案: Google Apps Script（使わなくてOK）

`attendance-api.gs` を script.google.com に貼り付けてデプロイする方法もあります。  
GitHub 方式の方が手順が少ないため、通常は上記だけで足ります。
