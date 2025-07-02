import dropbox
import os
import openai

DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

def save_and_process_file(file_path, content):
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)

    # ファイル保存
    dbx.files_upload(content.encode(), file_path, mode=dropbox.files.WriteMode.overwrite)

    # 内容の要約（OpenAIに送信）
    summary = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "次のファイルの内容を要約してください。"},
            {"role": "user", "content": content}
        ]
    )

    return summary['choices'][0]['message']['content']