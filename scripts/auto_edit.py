import os
import sys
import time
import yaml
from pathlib import Path

# 任意：Dropbox から変更ルールを拾いたい場合に使う
USE_DROPBOX = bool(os.getenv("DROPBOX_REFRESH_TOKEN") and os.getenv("DROPBOX_APP_KEY") and os.getenv("DROPBOX_APP_SECRET"))

RULES_LOCAL = Path("ops/desired_changes.yaml")
HEARTBEAT = Path("ops/last_run.log")

def load_rules():
    """
    1) リポジトリ内 ops/desired_changes.yaml を優先
    2) なければ（任意で）Dropbox から取得
    3) それも無ければデフォルトの簡易ルール
    """
    if RULES_LOCAL.exists():
        return yaml.safe_load(RULES_LOCAL.read_text(encoding="utf-8")) or {}

    if USE_DROPBOX:
        try:
            import dropbox
            dbx = dropbox.Dropbox(
                oauth2_refresh_token=os.environ["DROPBOX_REFRESH_TOKEN"],
                app_key=os.environ["DROPBOX_APP_KEY"],
                app_secret=os.environ["DROPBOX_APP_SECRET"],
            )
            # 例：/ops/desired_changes.yaml を探す
            path = "/ops/desired_changes.yaml"
            _, res = dbx.files_download(path)
            return yaml.safe_load(res.content.decode("utf-8")) or {}
        except Exception as e:
            print(f"[WARN] Failed to load rules from Dropbox: {e}")

    # デフォルト：何もしないけど heartbeat は更新される
    return {
        "edits": []
    }

def apply_edits(edits):
    """
    edits: 
      - file: "main.py"
        find: "SEND_LINE_SUMMARY = True"
        replace: "SEND_LINE_SUMMARY = False"
      - file: "README.md"
        insert_end: "\n\nAuto-edited at ..."
    """
    changed = False
    for rule in edits:
        fpath = Path(rule["file"])
        if not fpath.exists():
            print(f"[SKIP] {fpath} not found")
            continue

        text = fpath.read_text(encoding="utf-8")

        if "find" in rule and "replace" in rule:
            new_text = text.replace(rule["find"], rule["replace"])
            if new_text != text:
                fpath.write_text(new_text, encoding="utf-8")
                print(f"[EDIT] Replaced in {fpath}")
                changed = True

        if "insert_end" in rule:
            new_text = text + rule["insert_end"]
            if new_text != text:
                fpath.write_text(new_text, encoding="utf-8")
                print(f"[EDIT] Appended to {fpath}")
                changed = True

    return changed

def touch_heartbeat():
    HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    HEARTBEAT.write_text(f"last run: {ts}\n", encoding="utf-8")
    print(f"[OK] Heartbeat updated: {HEARTBEAT}")

def main():
    rules = load_rules()
    edits = rules.get("edits", [])
    changed = apply_edits(edits)
    # 何も編集がなくても heartbeat を更新 → GitHub に変更が出るようにしたいならここで追記でもOK
    touch_heartbeat()
    # commit/push は Workflow 側がやる
    print(f"[DONE] edited={changed}")

if __name__ == "__main__":
    sys.exit(main())
