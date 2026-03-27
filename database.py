# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Создаем папку для базы данных
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'tasks.db'}")

# Создаем движок для SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Создание таблиц"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print(f"✅ База данных создана: {DATABASE_URL}")