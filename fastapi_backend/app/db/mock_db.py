import json
import os

DB_FILE = "db.json"


def get_db():
    if not os.path.exists(DB_FILE):
        initial = {"users": {}, "passkeys": [], "challenges": {}}
        with open(DB_FILE, "w") as f:
            json.dump(initial, f, indent=4)
        return initial

    with open(DB_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {"users": {}, "passkeys": [], "challenges": {}}
        return json.loads(content)


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_user_by_username(username):
    db = get_db()
    for uid, data in db["users"].items():
        if data["username"] == username:
            return data
    return None