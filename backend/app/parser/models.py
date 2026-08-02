"""
MCRDSE Module 1 – IFC Parser Audit Persistence Model
=====================================================
SQLAlchemy ORM record storing file upload and parse history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ParsedIFCRecord(Base):
    """
    SQLAlchemy ORM record for storing IFC parse history and metadata.
    """

    __tablename__ = "parsed_ifc_records"

    parse_id = Column(String(36), primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    ifc_schema = Column(String(20), nullable=False)
    building_id = Column(String(50), nullable=False)
    building_name = Column(String(255), nullable=False)
    building_type = Column(String(100), nullable=False)
    floors = Column(Integer, nullable=False)
    height = Column(Float, nullable=False)
    builtup_area = Column(Float, nullable=False)
    plot_area = Column(Float, nullable=False)
    fsi = Column(Float, nullable=False)
    ground_coverage = Column(Float, nullable=False)
    parsed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    execution_time_ms = Column(Float, nullable=False)
