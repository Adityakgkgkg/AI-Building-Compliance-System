"""
AI Building Compliance System — Core Package

Exports the configuration and database utilities.
"""

from app.core.config import get_settings
from app.core.database import get_db, init_db, Base

__all__ = ["get_settings", "get_db", "init_db", "Base"]
