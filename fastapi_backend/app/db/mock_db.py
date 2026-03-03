# 1. Stores active challenges for verification: { "username": "base64_challenge_string" }
pending_challenges = {}

# 2. Stores user credentials: { "username": [{"id": b"...", "public_key": b"...", "sign_count": 0}] }
user_credentials = {}