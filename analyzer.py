import os
import dropbox_utils
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_file(content, filename=""):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "与えられたファイル内容を要約し、スロットの設定や傾向に関する分析を行ってください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ],
            temperature=0.4,
            max_tokens=1000
        )
        summary = response.choices[0].message.content.strip()
        return f"✅ {filename} の解析結果:\n{summary}"
    except Exception as e:
        return f"❌ {filename} の解析に失敗しました: {e}"

def run_analysis():
    messages = []
    files = dropbox_utils.list_files()
    
    for file in files:
        path = file.path_display
        content = dropbox_utils.download_file(path)
        if content:
            result = analyze_file(content, filename=file.name)
            messages.append(result)
    
    # 重複ファイルを整理
    dropbox_utils.find_duplicates()
    
    return messages
