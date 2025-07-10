# Dropbox × GPT × LINE Bot（OCR対応版）

このアプリは以下の機能を統合したAI解析BOTです：

- 📤 LINEからのテキスト or 画像送信をトリガーに
- 📦 Dropboxに保存されたファイルをGPTが自動解析
- 🧠 OCR（画像内の文字読み取り）にも対応
- 📲 LINEへ自動で解析結果を通知

---

## ✅ 主な構成

- フレームワーク: Flask（Renderで稼働）
- LINE API: Messaging API（Push対応）
- GPT API: OpenAI API v1.33.0
- Dropbox: Refresh Token対応（アクセストークン期限切れなし）
- OCR: easyOCR + torch（画像の文字認識）

---

## 🧪 動作フロー

1. LINEで「解析」や「分析」と送信
2. `Apps/slot-data-analyzer` フォルダ内のファイルをスキャン
3. テキスト or 画像の内容をAIが分析
   - 画像の場合はOCRも実行
4. 重複ファイルは除外 or 整理（ハッシュ比較）
5. 結果をLINEに送信

---

## 📁 必要な環境変数（Renderに設定）

| 環境変数名               | 説明 |
|--------------------------|------|
| `LINE_CHANNEL_SECRET`     | LINE Messaging APIのシークレット |
| `LINE_CHANNEL_ACCESS_TOKEN` | チャネルアクセストークン |
| `LINE_USER_ID`             | 通知送信用ユーザーID（Push） |
| `OPENAI_API_KEY`          | OpenAIのAPIキー |
| `DROPBOX_APP_KEY`         | Dropboxアプリのキー |
| `DROPBOX_APP_SECRET`      | Dropboxアプリのシークレット |
| `DROPBOX_REFRESH_TOKEN`   | Dropboxのリフレッシュトークン |

---

## 🧰 セットアップ（Render）

1. GitHubと連携してデプロイ
2. Web Serviceとして `/webhook` を有効化
3. `render.yaml` で自動ビルド対応
4. LINE Developers → Webhook URLを設定

---

## 🎯 拡張機能（今後の対応）

- Google Sheetsへの出力（任意）
- PDFやCSVのOCR処理
- フォルダ構成による自動タグ付け・整理
- LINEへの画像返信（生成画像）

---

## 📝 備考

- Dropbox無料プランでも動作確認済
- Render無料プラン（512MB RAM）でも稼働確認済
- 画像は 5MB 以下推奨、OCRは明瞭な文字画像に最適

---

## 📢 お問い合わせ

本Botは実験・学習目的で構築されました。
機能の追加や修正希望があれば開発者まで。