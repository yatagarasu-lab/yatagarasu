#!/usr/bin/env python3
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request

# ===== 設定（環境変数で上書き可） =====
BRANCH = os.getenv("BRANCH", "main")          # Repo Variable で設定済み
RUN_MODE = os.getenv("RUN_MODE", "auto")      # "auto" or "pr"
SERVICE_NAME = os.getenv("SERVICE_NAME", "")  # 任意（ログに出す）
DEPLOY_HOOK = (
    os.getenv("RENDER_DEPLOY_HOOK")           # 汎用名
    or os.getenv("YATAGARASU_DEPLOY_HOOK")    # 旧名（片方のRepo向け）
    or os.getenv("E_T_CODE_DEPLOY_HOOK")      # 旧名（もう片方のRepo向け）
)

ROOT = Path(__file__).resolve().parents[1]
OPS_DIR = ROOT / "ops"
LOG_FILE = OPS_DIR / "last_run.log"
VER_FILE = OPS_DIR / "auto" / "version.txt"

def sh(cmd: str):
    print(f"+ {cmd}")
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def git_config():
    # Actions からの push 用（checkout@v4 の資格情報を利用）
    user = os.getenv("GITHUB_ACTOR", "github-actions[bot]")
    email = f"{user}@users.noreply.github.com"
    sh(f'git config user.name "{user}"')
    sh(f'git config user.email "{email}"')

def ensure_files():
    OPS_DIR.mkdir(parents=True, exist_ok=True)
    (OPS_DIR / "auto").mkdir(parents=True, exist_ok=True)

def append_heartbeat():
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S %z")
    log_line = f"{now} [{SERVICE_NAME or 'service'}] heartbeat OK\n"
    LOG_FILE.write_text(LOG_FILE.read_text() + log_line if LOG_FILE.exists() else log_line, encoding="utf-8")
    print(f"wrote: {LOG_FILE}")

def bump_version_if_auto():
    if RUN_MODE.lower() != "auto":
        print("RUN_MODE != auto → version は更新しません")
        return
    current = 0
    if VER_FILE.exists():
        try:
            current = int(VER_FILE.read_text().strip() or "0")
        except Exception:
            current = 0
    VER_FILE.write_text(str(current + 1), encoding="utf-8")
    print(f"bumped: {VER_FILE} -> {current+1}")

def has_diff() -> bool:
    out = sh("git status --porcelain")
    return bool(out.strip())

def commit_and_push():
    sh("git add -A")
    if not has_diff():
        print("差分なし（コミットスキップ）")
        return False
    msg = f"chore(auto): heartbeat + patch ({RUN_MODE})"
    sh(f'git commit -m "{msg}"')
    # 念のためブランチに合わせて push
    sh(f"git push origin HEAD:{BRANCH}")
    print("pushed changes.")
    return True

def trigger_deploy():
    if not DEPLOY_HOOK:
        print("DEPLOY_HOOK 未設定（デプロイはスキップ）")
        return
    try:
        print(f"POST {DEPLOY_HOOK}")
        req = urllib.request.Request(DEPLOY_HOOK, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            print("deploy hook status:", r.status)
    except Exception as e:
        print("deploy hook error:", e)

def main():
    git_config()
    ensure_files()
    append_heartbeat()
    bump_version_if_auto()
    changed = commit_and_push()
    # 変更がなくても“定期的に”デプロイしたければ下を True に
    if changed:
        trigger_deploy()

if __name__ == "__main__":
    main()
