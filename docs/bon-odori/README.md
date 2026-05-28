# 晴海ふ頭公園盆踊り大会2026 公開ページ

このディレクトリは、GitHub Pagesで公開する盆踊り出店工程表です。

## ファイル

- `index.html`: 公開ページ本体
- `data.js`: 表示データ。更新は基本的にこのファイルを編集する
- `attendance.js`: 参加可否の入力・集計UI
- `attendance.json`: 共有用の参加可否データ（API未設定時のバックアップ）
- `attendance-api.gs`: 自動共有用 Google Apps Script（1回セットアップ）
- `ATTENDANCE_SYNC.md`: 自動共有のセットアップ手順
- `assets/venue-map.png`, `assets/venue-map.pdf`: 事務局確定の会場図（サマリータブで表示）

## 更新方法

1. `data.js` を編集する
2. `updatedAt` を更新する
3. GitHubにpushする
4. GitHub Pagesの反映を待つ

## 参加可否の使い方

1. 公開ページの「参加・回答」タブで、**個人名**ごとに入力する
2. 7/11・7/12それぞれについて、参加可否と11〜22時の1時間枠（複数選択）を選ぶ
3. 担当は「調理・店頭業務・子供のケア・全般」から選択する（未定可）
4. **回答を保存** — 自動共有が有効なら全員に反映（JSON不要）
5. 自動共有が未設定のときだけ、JSONエクスポート／取り込みで統合

### 全員への自動共有（推奨）

`ATTENDANCE_SYNC.md` の手順で Google Apps Script をデプロイし、発行 URL を `data.js` の `attendanceApiUrl` に設定する。

- 保存 → 即時にクラウドへ送信
- 他の人の画面 → 約30秒ごとに自動取得（タブを開いている間）

## 共有URL（LINE用）

**こちらだけを共有してください（青×白の最新版）:**

https://del10ro17-debug.github.io/bon-odori-roadmap/bon-odori/

`company/projects/bon-odori-harumi-2026/team-share.html` はローカル用の旧ファイルです。Finder から開くとオレンジの古い画面が出ます。

## 公開前の注意

- 個人情報、内部連絡先、メールアドレス、売上見込みなどは載せない
- 公開してよい内容だけに絞る
- 詳細な内部運営情報は `company/projects/bon-odori-harumi-2026/` 側で管理する

## GitHub Pages設定

GitHub上で以下を設定する。

1. Repository Settings を開く
2. Pages を開く
3. Source を `Deploy from a branch` にする
4. Branch を `main`、Folder を `/docs` にする
5. 表示されたURLをLINEに共有する
