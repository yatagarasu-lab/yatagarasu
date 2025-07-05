import dropbox
import hashlib

# アクセストークンをここに記載
DROPBOX_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

def analyze_dropbox_updates():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

    folder_path = "/Apps/slot-data-analyzer"
    files = dbx.files_list_folder(folder_path).entries

    seen_hashes = {}
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            content, _ = dbx.files_download(file.path_display)
            file_bytes = content.content
            file_hash = hashlib.md5(file_bytes).hexdigest()

            if file_hash in seen_hashes:
                print(f"重複ファイル削除: {file.path_display}")
                dbx.files_delete_v2(file.path_display)
            else:
                seen_hashes[file_hash] = file.path_display
                print(f"保存: {file.name}")