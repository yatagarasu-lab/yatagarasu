# gpt_handler.py
import openai
import hashlib
import json
import time
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

# ファイルの内容を判別して「スロット関連」か確認
def is_slot_related(text):
    slot_keywords = ["スロット", "設定", "差枚", "北斗", "番長", "ジャグラー", "グラフ", "CZ", "AT", "パチスロ", "解析"]
    return any(keyword in text for keyword in slot_keywords)

# GPTで要約・スロット関連確認
def analyze_file_with_gpt(file_name, content):
    try:
        result = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはスロットの専門家です。送られた情報がスロットに関する内容かを確認し、関連あれば要点を要約してください。スロットに無関係なら『これはスロットと無関係です』と返してください。"},
                {"role": "user", "content": content[:4000]}
            ]
        )
        reply = result.choices[0].message.content.strip()
        return reply
    except Exception as e:
        return f"[GPTエラー]: {str(e)}"