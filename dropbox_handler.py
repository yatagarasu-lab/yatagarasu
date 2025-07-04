import dropbox
import hashlib
import os
import io

# Dropbox アクセストークン（環境変数から取得）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


def list_files(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox内の指定フォルダにあるファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"❌ Dropboxファイル一覧取得エラー: {e}")
        return []


def download_file(path: str) -> bytes:
    """Dropboxからファイルをダウンロード（バイナリで返す）"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"❌ Dropboxファイルダウンロードエラー（{path}）: {e}")
        return b""


def file_hash(content: bytes) -> str:
    """ファイルのSHA-256ハッシュ値を計算"""
    return hashlib.sha256(content).hexdigest()


def delete_file(path: str) -> None:
    """Dropbox上のファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"🗑️ 削除完了: {path}")
    except Exception as e:
        print(f"⚠️ ファイル削除失敗（{path}）: {e}")


def upload_file(file_path: str, dropbox_path: str) -> None:
    """ローカルファイルをDropboxにアップロード"""
    try:
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ アップロード完了: {file_path} → {dropbox_path}")
    except Exception as e:
        print(f"❌ アップロード失敗（{file_path}）: {e}")