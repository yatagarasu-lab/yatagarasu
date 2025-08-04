import hashlib
import os
import json

CACHE_FILE = "file_cache.json"

class FileCache:
    def __init__(self):
        if not os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "w") as f:
                json.dump({}, f)
        with open(CACHE_FILE, "r") as f:
            self.cache = json.load(f)

    def is_duplicate(self, path, content_hash):
        return self.cache.get(path) == content_hash

    def update(self, path, content_hash):
        self.cache[path] = content_hash
        with open(CACHE_FILE, "w") as f:
            json.dump(self.cache, f)
