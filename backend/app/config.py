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
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", os.getenv("SUPABASE_KEY", ""))
    
    # Embeddings & Vector Search (Local BAAI/bge-small-en-v1.5)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # LLM Provider Selection ("groq" or "xai")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")

    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # xAI / Grok API Configuration (Preserved)
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
