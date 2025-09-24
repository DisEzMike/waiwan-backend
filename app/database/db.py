from __future__ import annotations
import contextlib
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from ..utils.config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DBNAME


if not all([PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DBNAME]):
    raise RuntimeError("PostgreSQL env vars are not fully set")

DATABASE_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

class Base(DeclarativeBase):
    pass

class DB:
    """
    จัดการ Engine/Session + ensure pgvector
    ใช้เป็น dependency และใน startup event
    """
    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url, pool_pre_ping=True, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, class_=Session, future=True)

    def init_extensions(self) -> None:
        # เปิดใช้งาน pgvector หากยังไม่ได้เปิด
        with self.engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    def create_all(self) -> None:
        from .models.users import Users, UserProfiles
        from .models.senior_users import SeniorUsers, SeniorProfiles, SeniorAbilities
        from .models.jobs import Jobs, Status
        from .models.reviews import Reviews
        from .models.files import Files
        Base.metadata.create_all(bind=self.engine)

    @contextlib.contextmanager
    def session(self) -> Generator[Session, None, None]:
        db: Session = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

db = DB()