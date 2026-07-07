import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).parent.parent
CHROMA_PATH = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "goethe_texts"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = os.getenv("GOETHE_CHAT_MODEL", "gpt-4o-mini")
TTS_MODEL = "tts-1"
TTS_VOICE = os.getenv("GOETHE_TTS_VOICE", "onyx")

RETRIEVAL_TOP_K = 6
MEMORY_TURNS = 3  # number of prior user/assistant exchanges kept as context

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
