# github_utils.py
import os
import base64
import json
import requests
from typing import Optional, Dict, List, Tuple

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "owner/repo"
GITHUB_DEFAULT_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME", "Auto Bot")
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "bot@example.com")

API_BASE = "https://api.github.com"

class GitHubError(Exception):
    pass

def _headers():
    if not GITHUB_TOKEN:
        raise GitHubError("GITHUB_TOKEN が未設定です。")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "auto-committer"
    }

def _repo_api(path: str) -> str:
    if not GITHUB_REPO:
        raise GitHubError("GITHUB_REPO（owner/repo）が未設定です。")
    return f"{API_BASE}/repos/{GITHUB_REPO}{path}"

def get_file_sha(path: str, ref: Optional[str] = None) -> Optional[str]:
    """既存ファイルのSHAを取得（無い場合はNone）"""
    url = _repo_api(f"/contents/{path}")
    params = {"ref": ref or GITHUB_DEFAULT_BRANCH}
    r = requests.get(url, headers=_headers(), params=params, timeout=20)
    if r.status_code == 200:
        return r.json().get("sha")
    if r.status_code == 404:
        return None
    raise GitHubError(f"get_file_sha failed: {r.status_code} {r.text}")

def put_file(
    path: str,
    content_bytes: bytes,
    message: str,
    branch: Optional[str] = None,
    sha: Optional[str] = None
) -> Dict:
    """/contents APIで単一ファイルを作成/更新"""
    url = _repo_api(f"/contents/{path}")
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8"),
        "branch": branch or GITHUB_DEFAULT_BRANCH,
        "committer": {"name": GIT_AUTHOR_NAME, "email": GIT_AUTHOR_EMAIL}
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=_headers(), data=json.dumps(payload), timeout=30)
    if r.status_code in (200, 201):
        return r.json()
    raise GitHubError(f"put_file failed: {r.status_code} {r.text}")

def commit_text(
    repo_path: str,
    text: str,
    commit_message: str
) -> str:
    """テキストを指定パスへコミット（新規/更新を自動判定）"""
    sha = get_file_sha(repo_path)
    resp = put_file(
        path=repo_path,
        content_bytes=text.encode("utf-8"),
        message=commit_message,
        sha=sha
    )
    return f"✅ GitHub push: {repo_path} ({'update' if sha else 'create'})"

def commit_files(
    files: List[Tuple[str, bytes]],
    commit_message: str
) -> List[str]:
    """
    複数ファイルを/contents APIで順次コミット
    files: [(repo_path, content_bytes), ...]
    """
    results = []
    for repo_path, content in files:
        sha = get_file_sha(repo_path)
        put_file(
            path=repo_path,
            content_bytes=content,
            message=commit_message,
            sha=sha
        )
        results.append(f"{repo_path}: {'update' if sha else 'create'}")
    return results
