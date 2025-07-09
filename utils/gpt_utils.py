import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_and_tag_text(text):
    """
    GPTで要約とタグ付けを行う
    """
    try:
        system_prompt = (
            "以下のテキストから要点を簡潔にまとめて、"
            "最後に関連するキーワードをハッシュタグ形式で3つ付けてください。"
        )
        user_prompt = f"内容：\n{text}"

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[GPT要約失敗] {e}"
