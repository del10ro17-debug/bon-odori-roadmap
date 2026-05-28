# 晴海ふ頭公園盆踊り大会2026 公開ページ

このディレクトリは、GitHub Pagesで公開する盆踊り出店工程表です。

## ファイル

- `index.html`: 公開ページ本体
- `data.js`: 表示データ。更新は基本的にこのファイルを編集する
- `attendance.js`: 参加可否の入力・集計UI
- `attendance.json`: 共有用の参加可否データ（GitHubへコミットすると全員に反映）

## 更新方法

1. `data.js` を編集する
2. `updatedAt` を更新する
3. GitHubにpushする
4. GitHub Pagesの反映を待つ

## 参加可否の使い方

1. 公開ページの「参加・回答」タブで、**個人名**ごとに入力する
2. 7/11・7/12それぞれについて、参加可否と11〜22時の1時間枠（複数選択）を選ぶ
3. 担当は「調理・店頭業務・子供のケア・全般」から選択する（未定可）
4. 集計表と参加/不可/未定の件数が自動表示される
3. 坂倉・竹山家は「JSONをエクスポート」「JSONを取り込む」で複数端末の回答を統合できる
4. 全員に同じ状態を見せたいときは、統合後の JSON を `attendance.json` に貼り付けてコミットする

### 全員リアルタイム同期（任意）

Google Apps Script をデプロイし、発行された URL を `data.js` の `attendanceApiUrl` に設定すると、保存時に全員の画面へ即時反映できます。

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
