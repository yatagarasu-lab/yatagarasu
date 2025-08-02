# --- Dropbox to GoogleDrive Task ---
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import dropbox
import os
import io

def transfer_dropbox_to_gdrive():
    try:
        # Dropbox 認証
        dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
        dropbox_path = "/Apps/slot-data-analyzer"
        entries = dbx.files_list_folder(dropbox_path).entries

        # Google Drive 認証
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        drive = GoogleDrive(gauth)

        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                file_path = entry.path_display
                _, ext = os.path.splitext(file_path)
                _, res = dbx.files_download(file_path)
                content = res.content

                gfile = drive.CreateFile({'title': os.path.basename(file_path)})
                if ext in ['.txt', '.csv', '.json']:
                    gfile.SetContentString(content.decode())
                else:
                    gfile.SetContentString("バイナリファイル（省略）")
                gfile.Upload()
    except Exception as e:
        print("転送エラー:", str(e))