import os
import sys
import pathlib
import datetime
import dropbox

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY       = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET    = os.getenv("DROPBOX_APP_SECRET")

DROPBOX_FOLDER = os.getenv("DROPBOX_FOLDER", "/")        # 例: "/" or "/inbox"
SYNC_DIR       = os.getenv("SYNC_DIR", "dropbox_sync")   # リポジトリ内に作る保存先

if not (DROPBOX_REFRESH_TOKEN and DROPBOX_APP_KEY and DROPBOX_APP_SECRET):
    print("❌ Missing Dropbox credentials in env.", file=sys.stderr)
    sys.exit(1)

root = pathlib.Path(SYNC_DIR)
root.mkdir(parents=True, exist_ok=True)

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
)

def safe_join(base: pathlib.Path, *parts: str) -> pathlib.Path:
    p = base.joinpath(*[s.strip("/").replace("..", "_") for s in parts if s])
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def list_entries(folder: str):
    res = dbx.files_list_folder(folder, recursive=True)
    for e in res.entries:
        yield e
    while res.has_more:
        res = dbx.files_list_folder_continue(res.cursor)
        for e in res.entries:
            yield e

count_dl = 0
for entry in list_entries("" if DROPBOX_FOLDER in ("", "/") else DROPBOX_FOLDER):
    # フォルダ/削除済みはスキップ
    if isinstance(entry, dropbox.files.FileMetadata):
        path_display = entry.path_display or entry.path_lower
        rel = path_display.lstrip("/")  # リポジトリ内の相対パス
        # 保存先は dropbox_sync/<元のパス>
        local_path = safe_join(root, rel)

        try:
            md, resp = dbx.files_download(entry.path_lower)
            data = resp.content
            # 既存と同一内容ならスキップ
            if local_path.exists() and local_path.read_bytes() == data:
                continue
            local_path.write_bytes(data)
            count_dl += 1
            print(f"✔ Downloaded: {path_display} -> {local_path}")
        except Exception as e:
            print(f"⚠ Failed: {path_display}: {e}", file=sys.stderr)

timestamp = datetime.datetime.utcnow().isoformat() + "Z"
print(f"Done. Updated files: {count_dl} at {timestamp}")
