def is_image(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg'))

def is_text(filename):
    return filename.lower().endswith('.txt')

def list_and_filter_files():
    files = list_files(DROPBOX_FOLDER_PATH)
    image_files = [f for f in files if is_image(f.name)]
    text_files = [f for f in files if is_text(f.name)]
    return image_files, text_files

def move_file_to_archive(path):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(path)
        new_path = f"{DROPBOX_ARCHIVE_PATH}/{timestamp}_{filename}"
        dbx.files_move_v2(path, new_path)
        print(f"[move_file_to_archive] Moved {path} -> {new_path}")
        return new_path
    except Exception as e:
        print(f"[move_file_to_archive] Error: {e}")
        return path