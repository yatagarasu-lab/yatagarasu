# analyze_and_notify.py

from gpt_handler import analyze_file_and_notify
from dropbox_handler import list_files

def analyze_dropbox_updates():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    
    for file in files:
        path = file.path_display
        analyze_file_and_notify(path)