# Dropbox × LINE × GPT解析BOT

このアプリは、以下の機能を提供します：

- LINE BOTからの受信
- Dropbox Webhookによる自動解析通知
- GPTによる自動要約・重複チェック
- Push通知でLINEに結果報告

## デプロイ手順（Render）

1. GitHubと連携
2. Renderで新しいWebサービス作成
3. `render.yaml` を指定して自動構築
4. 環境変数を設定
5. 動作確認（LINE, Dropbox両方）

## 必要な環境変数

- `DROPBOX_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`