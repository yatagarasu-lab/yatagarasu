from services.gpt_summarizer import summarize_file_and_notify

# DropboxのWebhookが呼び出されたときに実行する関数
def handle_dropbox_webhook():
    print("📦 Dropbox Webhook受信。解析処理を開始します。")
    summarize_file_and_notify()
    return "✅ Dropboxファイルの解析と通知が完了しました。"
