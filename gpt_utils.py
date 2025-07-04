import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def process_with_gpt_text(text: str) -> str:
    """テキストをGPTで要約・分類"""
    prompt = (
        "以下のスロット関連の情報を要約し、機種名・台番号・示唆内容・設定推測（高設定・中間・低設定）などを明確に分類してください：\n\n"
        f"{text}\n\n"
        "出力は簡潔にまとめてください。"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"GPT解析エラー: {str(e)}"

def process_with_gpt_image(image_bytes: bytes) -> str:
    """画像をOCR＋GPTで処理し要約（画像内のテキストを読み取って解析）"""
    try:
        # 画像内のテキストをOCRとして読み取ってGPTに渡す（例：Base64処理なども可能）
        prompt = (
            "以下はスロットの実戦報告や示唆画面の画像です。読み取れる内容を要約し、示唆内容や設定推測を明記してください。"
        )
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_bytes.decode()}}
                ]}
            ],
            max_tokens=1000
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"画像解析エラー: {str(e)}"