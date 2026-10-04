import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip().replace("GROQ_MODEL=", "", 1)
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./database.db")

    def __init__(self):
        # Create upload directory if it does not exist
        if not os.path.exists(self.UPLOAD_DIR):
            os.makedirs(self.UPLOAD_DIR, exist_ok=True)
            
        # Create a subfolder for charts inside uploads
        charts_dir = os.path.join(self.UPLOAD_DIR, "charts")
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir, exist_ok=True)

settings = Settings()
