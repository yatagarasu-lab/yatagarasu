# Dropbox × LINE × GPT解析BOT

このBOTは、LINEで受け取ったメッセージをトリガーに、Dropbox上のファイルをGPTで自動解析し、その結果をLINEへ返信・通知するシステムです。

---

## 🔧 構成技術

- Python + Flask（Renderにデプロイ）
- LINE Messaging API（双方向応答＋Push通知）
- Dropbox API（リフレッシュトークン対応）
- OpenAI GPT API（テキスト・画像の解析対応）
- OCR対応（画像文字認識も可能）
- Renderデプロイ対応（無料プラン可）

---

## 🌐 使用手順（概要）

1. このリポジトリを GitHub で Fork（もしくはクローン）
2. `.env.template` を `.env` にリネームし、各種APIキーを入力
3. Renderにデプロイ（`render.yaml` で自動設定可能）
4. LINE Developers でWebhook URLを設定（例: `https://xxx.onrender.com/webhook`）
5. DropboxのWebhookも設定（`/webhook`にPOST）

---

## 🧪 テスト方法

### 🔁 LINE返信テスト

LINEで「解析」や「分析」と送信 → Dropboxの解析結果がLINEで返信されます。

### 🧠 GPTによる自動解析

1. Dropboxにファイル追加（画像やテキスト）
2. Webhookが作動 → GPTが内容を分析
3. 指定LINEユーザーに通知メッセージをPush

---

## 📁 フォルダ構成（主な構成）