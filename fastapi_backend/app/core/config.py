import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# --- DYNAMIC VARIABLES (Loaded from .env) ---
# We use os.getenv("VARIABLE_NAME", "fallback_value") just in case the .env is missing
RP_ID = os.getenv("RP_ID", "localhost")
ORIGIN = os.getenv("ORIGIN", "http://127.0.0.1:3000")
SECRET_CHALLENGE_KEY = os.getenv("SECRET_CHALLENGE_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# --- STATIC CONFIGURATION (Stays in code) ---
RP_NAME = "Pitch Pass API"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours