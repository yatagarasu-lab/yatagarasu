import dropbox
import os
import hashlib
import io
import zipfile

# Dropboxアクセストークン（環境変数から取得）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path):
    """指定フォルダ内のファイル一覧を取得"""
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print(f"Dropbox list_files エラー: {e}")
        return []

def download_file(path):
    """Dropboxからファイルをダウンロード（バイナリで返す）"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"Dropbox download エラー: {e}")
        return b""

def upload_file(path, content):
    """Dropboxへファイルをアップロード"""
    try:
        dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ アップロード成功: {path}")
    except Exception as e:
        print(f"Dropbox upload エラー: {e}")

def delete_file(path):
    """Dropbox上のファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"🗑️ 削除完了: {path}")
    except Exception as e:
        print(f"Dropbox delete エラー: {e}")

def file_hash(content):
    """ファイル内容からSHA256ハッシュを生成"""
    return hashlib.sha256(content).hexdigest()

def compress_and_upload_zip(files: list, zip_path="/Apps/slot-data-analyzer/latest_upload.zip"):
    """
    与えられたファイルパスリストをZIPにまとめ、Dropboxへアップロード
    files: Dropbox内のファイルパス（例: /Apps/slot-data-analyzer/xxx.txt）
    """
    try:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in files:
                filename = os.path.basename(path)
                content = download_file(path)
                if content:
                    zipf.writestr(filename, content)

        buffer.seek(0)
        upload_file(zip_path, buffer.read())
        print("✅ 圧縮とアップロード完了")
    except Exception as e:
        print(f"ZIP圧縮エラー: {e}")