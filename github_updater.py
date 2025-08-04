import os
import requests
import base64

def update_github_file(file_path: str, new_content: str, commit_message: str = "Update from Render"):
    token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.get(api_url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"GitHubファイル取得失敗: {res.text}")
    sha = res.json()["sha"]

    encoded_content = base64.b64encode(new_content.encode()).decode()
    data = {
        "message": commit_message,
        "content": encoded_content,
        "sha": sha
    }

    response = requests.put(api_url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        print("✅ GitHubファイル更新成功")
    else:
        print("❌ GitHubファイル更新失敗:", response.text)
