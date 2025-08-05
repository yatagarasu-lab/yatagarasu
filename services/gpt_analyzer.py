import os
import dropbox
import openai
from line_notifier import send_line_message

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_and_notify(dbx, file_path):
    try:
        # ファイルのダウンロード
        _, res = dbx.files_download(file_path)
        content = res.content.decode("utf-8")

        # GPTで解析
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のデータを要約・解析し、簡潔にレポートを出力してください。"},
                {"role": "user", "content": content}
            ],
            max_tokens=1000,
            temperature=0.5
        )

        summary = response["choices"][0]["message"]["content"]

        # LINEに送信
        send_line_message(f"✅ファイル解析完了\n📄ファイル名: {file_path}\n\n📝解析結果:\n{summary}")

    except Exception as e:
        print(f"[gpt_analyzer] エラー発生: {e}")
        send_line_message("⚠️ GPT解析中にエラーが発生しました。ログを確認してください。")
