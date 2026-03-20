RP_ID = "localhost"  # Change to your domain in production (e.g., api.yourdomain.com)
RP_NAME = "Pitch Pass API"
ORIGIN = "http://localhost:3000"  # The origin of your web frontend or mobile app link
SECRET_CHALLENGE_KEY = "my_secret_key"  # The origin of your web frontend or mobile app link

# JWT Configuration
# In production, use a strong random string (e.g., run `openssl rand -hex 32`)
JWT_SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours