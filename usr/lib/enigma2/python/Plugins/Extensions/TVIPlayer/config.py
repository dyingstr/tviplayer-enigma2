import json
import os

CONFIG_PATH = "/etc/enigma2/tviplayer.json"


def load_config():
    """Load credentials from /etc/enigma2/tviplayer.json.
    Returns dict with 'email' and 'password', or None on error.
    """
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if "email" in data and "password" in data:
            return data
        return None
    except Exception:
        return None
