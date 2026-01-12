import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
WEB_URL = os.getenv("WEB_URL", "http://localhost:8000")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", 0))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


