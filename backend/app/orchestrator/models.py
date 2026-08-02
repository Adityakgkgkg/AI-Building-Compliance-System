"""
MCRDSE Analysis Orchestrator – ORM Models
===========================================
SQLAlchemy ORM database table for persisting analysis run records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()



class AnalysisRecord(Base):
    """
    Persisted record of an automated end-to-end analysis run.
    """

    __tablename__ = "analysis_records"

    analysis_id = Column(String(36), primary_key=True, index=True)
    ifc_file = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="running")
    current_stage = Column(String(100), nullable=False, default="Uploading")
    progress = Column(Integer, nullable=False, default=0)
    
    building_id = Column(String(255), nullable=True)
    building_name = Column(String(255), nullable=True)
    sanction_verdict = Column(String(255), nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    total_processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_detail = Column(Text, nullable=True)
