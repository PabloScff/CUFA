from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import carregar

settings = carregar()

_url = settings.database_url
for _prefixo in ("postgres://", "postgresql://"):
    if _url.startswith(_prefixo):
        _url = "postgresql+psycopg2://" + _url[len(_prefixo):]  # usa o driver psycopg2-binary
        break

_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}
engine = create_engine(_url, connect_args=_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()