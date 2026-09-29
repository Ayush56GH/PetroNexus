import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    PROJECT_NAME: str = "PetroNexus"
    PROJECT_TAGLINE: str = "Connect the Well. Remember the Past. Anticipate the Next."
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    # Secret Key for JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "petronexus-super-secure-production-ready-jwt-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/petronexus.db")
    
    # xAI / Grok API
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    GROK_MODEL: str = os.getenv("GROK_MODEL", "grok-2-latest")
    
    # File storage paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DOCUMENTS_DIR: Path = BASE_DIR / "documents"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    DATA_DIR: Path = BASE_DIR / "data"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
