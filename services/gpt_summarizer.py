import openai
from config import OPENAI_API_KEY, GPT_MODEL

openai.api_key = OPENAI_API_KEY

def summarize_content(text):
    prompt = f"次の文章を要約してください:\n\n{text[:2000]}"
    
    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=512
    )

    return response['choices'][0]['message']['content'].strip()