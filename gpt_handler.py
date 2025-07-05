# gpt_handler.py

from openai import OpenAI
from dropbox_handler import download_file

client = OpenAI()

def analyze_file_and_notify(file_path):
    content = download_file(file_path)
    content_str = content.decode("utf-8")

    prompt = f"このファイルの内容を要約し、重要な点を箇条書きで教えてください:\n\n{content_str}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    summary = response.choices[0].message.content
    print(f"要約:\n{summary}")