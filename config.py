import os
from dotenv import load_dotenv

load_dotenv()

DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# GPT設定
GPT_MODEL = "gpt-4o"