# dropbox_handler.py

import os
import base64
import requests
from datetime import datetime

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR", "GPT Bot <bot@example.com>")

# GitHubに自動Push（dropbox_updatesディレクトリ用）
def push_summary_to_github(summary_text):
    try:
        filename = f"dropbox_updates/{datetime.now().strftime('%Y-%m-%d_%H-%M')}_summary.md"
        commit_message = f"自動更新: Dropboxファイル要約（{filename}）"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 既存ファイル確認（存在していたらSHAを取得）
        sha = None
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            sha = resp.json().get("sha")

        payload = {
            "message": commit_message,
            "content": base64.b64encode(summary_text.encode()).decode(),
            "branch": GITHUB_BRANCH,
            "committer": {
                "name": GITHUB_COMMIT_AUTHOR.split("<")[0].strip(),
                "email": GITHUB_COMMIT_AUTHOR.split("<")[1].replace(">", "").strip()
            }
        }
        if sha:
            payload["sha"] = sha

        result = requests.put(url, headers=headers, json=payload)
        return result.status_code in [200, 201], result.json() if result.status_code in [200, 201] else result.text

    except Exception as e:
        return False, str(e)