import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN not set in .env file")

SCAM_IMAGES_DIR = os.getenv("SCAM_IMAGES_DIR", "img")
DELETED_IMAGES_DIR = os.getenv("DELETED_IMAGES_DIR", "deleted")
SIMILARITY_THRESHOLD = int(os.getenv("SIMILARITY_THRESHOLD", "16"))
GUILD_CONFIG_FILE = os.getenv("GUILD_CONFIG_FILE", "guild_config.json")
