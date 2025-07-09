import openai

def summarize_and_tag_text(text: str):
    try:
        system_prompt = (
            "あなたは、Dropboxに追加されたスロットに関する情報を分析するAIです。\n"
            "入力されたテキストをできるだけ短く要約し、重要なキーワード（機種名、台番、示唆内容など）を抽出してください。\n"
            "出力形式は以下：\n\n"
            "【要約】\n...\n\n【タグ】\n...\n"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"[要約失敗]: {e}"