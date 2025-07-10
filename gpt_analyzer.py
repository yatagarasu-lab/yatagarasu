import os
import io
from dropbox_utils import list_files, download_file, file_hash, delete_file
from PIL import Image
import pytz
from datetime import datetime
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage
import mimetypes
import hashlib

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))

# インスタンス
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ファイル重複判定用ハッシュ記録
hash_map = {}

def analyze_dropbox_and_notify():
    """Dropbox内のファイルを解析してLINEに通知"""
    entries = list_files()
    results = []
    for entry in entries:
        path = entry.path_display
        content = download_file(path)
        h = file_hash(content)

        if h in hash_map:
            delete_file(path)  # 重複ファイル削除
            continue
        else:
            hash_map[h] = path

        result = analyze_content(path, content)
        results.append(result)

    summary = "\n\n".join(results) if results else "新しい解析対象がありませんでした。"
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=summary))


def analyze_content(path, content):
    """ファイル内容をGPTで解析（画像 or テキスト）"""
    mime_type, _ = mimetypes.guess_type(path)

    if mime_type and mime_type.startswith("image/"):
        return analyze_image(path, content)
    else:
        return analyze_text(path, content)


def analyze_text(path, content):
    """テキストファイルをGPTで要約"""
    try:
        text = content.decode("utf-8")
    except:
        return f"[{path}] テキスト解析失敗（文字コード不明）"

    prompt = f"次の内容を要約してください：\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
    )
    summary = response.choices[0].message.content.strip()
    return f"[{path}]\n{summary}"


def analyze_image(path, content):
    """画像ファイルをOCR＋要約"""
    try:
        image = Image.open(io.BytesIO(content))
        import easyocr
        reader = easyocr.Reader(["ja", "en"], gpu=False)
        result = reader.readtext(content, detail=0)
        text = "\n".join(result)
    except:
        return f"[{path}] 画像解析失敗（読み込みエラー）"

    if not text.strip():
        return f"[{path}] 画像内に文字が見つかりませんでした。"

    prompt = f"次の画像内のテキストを要約してください：\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
    )
    summary = response.choices[0].message.content.strip()
    return f"[{path}]\n{summary}"