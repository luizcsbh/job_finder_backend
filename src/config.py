import os

from dotenv import load_dotenv

load_dotenv()


STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "sqlite").lower()
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "database.db")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_USERS_TABLE = os.getenv("SUPABASE_USERS_TABLE", "users")
SUPABASE_FAVORITES_TABLE = os.getenv("SUPABASE_FAVORITES_TABLE", "favorites")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173"
    ).split(",")
    if origin.strip()
]
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(5 * 1024 * 1024)))

# Admin and Security
MASTER_ADMIN_EMAIL = os.getenv("MASTER_ADMIN_EMAIL", "luizsantos@example.com")
# A secret key only the dev knows to force admin access
DEVELOPER_MASTER_KEY = os.getenv("DEVELOPER_MASTER_KEY", "dev_secret_2026_master")
