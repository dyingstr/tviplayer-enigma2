import os
import hashlib
import threading
import urllib.request

CACHE_DIR = "/tmp/tviplayer_cache"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)


def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        try:
            os.makedirs(CACHE_DIR)
        except OSError:
            pass


def cache_path(url):
    """Return the local file path for a given thumbnail URL."""
    key = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, key + ".jpg")


def fetch_thumb(url, callback):
    """Download a thumbnail asynchronously.

    If already cached, calls callback(path) immediately in the same thread.
    Otherwise downloads in a background thread and calls callback(path) when done.
    callback receives the local file path on success, or None on failure.
    """
    if not url:
        callback(None)
        return

    path = cache_path(url)
    if os.path.exists(path):
        callback(path)
        return

    def _download():
        _ensure_cache_dir()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
            callback(path)
        except Exception:
            callback(None)

    t = threading.Thread(target=_download, daemon=True)
    t.start()


def clear_cache():
    """Remove all cached thumbnails."""
    if not os.path.exists(CACHE_DIR):
        return
    for fname in os.listdir(CACHE_DIR):
        if fname.endswith(".jpg"):
            try:
                os.remove(os.path.join(CACHE_DIR, fname))
            except OSError:
                pass
