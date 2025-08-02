import requests
from dropbox_auth import get_access_token

def upload_to_dropbox(file_path, dropbox_path):
    access_token = get_access_token()

    with open(file_path, "rb") as f:
        data = f.read()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": str({
            "path": dropbox_path,
            "mode": "overwrite",
            "autorename": False,
            "mute": False
        }).replace("'", '"'),
        "Content-Type": "application/octet-stream"
    }

    response = requests.post("https://content.dropboxapi.com/2/files/upload", headers=headers, data=data)
    response.raise_for_status()
    print("✅ アップロード成功:", dropbox_path)

def read_from_dropbox(dropbox_path):
    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": str({ "path": dropbox_path }).replace("'", '"')
    }

    response = requests.post("https://content.dropboxapi.com/2/files/download", headers=headers)
    response.raise_for_status()
    return response.content.decode("utf-8")
