import openai
import os
import hashlib
import dropbox

# 環境変数からキー取得
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

openai.api_key = OPENAI_API_KEY
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 既読ファイル用のハッシュ記録用セット（オンメモリ簡易版）
seen_hashes = set()

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def process_with_gpt(text: str) -> str:
    """送られたテキストをGPTで要約してDropboxに保存、LINE通知も送る"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "スロットのデータを解析して要点を簡潔にまとめてください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=500
        )
        summary = response.choices[0].message.content.strip()

        # Dropboxに保存（要約結果）
        filename = f"/スロットデータ/summary_{hashlib.md5(text.encode()).hexdigest()}.txt"
        dbx.files_upload(summary.encode(), filename, mode=dropbox.files.WriteMode.overwrite)

        # LINEに通知
        send_line_push_message("GPT解析結果：\n" + summary)

        return summary

    except Exception as e:
        error_msg = f"GPT処理でエラーが発生しました: {str(e)}"
        send_line_push_message(error_msg)
        return error_msg

def send_line_push_message(message: str):
    """LINEのPush通知"""
    import requests

    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)