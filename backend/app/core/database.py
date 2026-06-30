"""
AI Building Compliance System — Database Configuration

SQLAlchemy engine and session factory for SQLite.
In Sprint 2+, ORM models will be registered against `Base` and
tables will be created via `init_db()`.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# ── Engine ───────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=settings.DEBUG,
)

# ── Session Factory ──────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative Base ─────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all ORM models.

    Sprint 2+ models (Building, ComplianceReport, etc.) will inherit from this.
    """
    pass


# ── Dependency ───────────────────────────────────────────────────
def get_db():
    """FastAPI dependency that yields a database session.

    Usage:
        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Initialization ──────────────────────────────────────────────
def init_db() -> None:
    """Create all tables defined by ORM models.

    Call this at application startup. Currently a no-op since
    no models are registered yet.
    """
    Base.metadata.create_all(bind=engine)
