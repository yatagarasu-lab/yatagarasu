import dropbox
import os

# Dropbox アクセストークンは .env から取得
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_file(local_path, dropbox_path):
    """
    ローカルファイルをDropboxにアップロードする関数
    :param local_path: 保存済みのローカルパス（例: /tmp/abc.jpg）
    :param dropbox_path: アップロード先のDropboxパス（例: /Apps/slot-data-analyzer/images/abc.jpg）
    """
    try:
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ アップロード完了: {dropbox_path}")
    except Exception as e:
        print(f"❌ アップロード失敗: {e}")
        raise e