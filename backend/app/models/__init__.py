"""
AI Building Compliance System — ORM Models

This package contains SQLAlchemy ORM models:
  - Sprint 1: (none)
  - Sprint 2: ComplianceReportRecord (compliance_reports table)
  - Future: GISContext, UrbanZone

All models inherit from `app.core.database.Base`.
Importing them here ensures `Base.metadata.create_all()` sees them.
"""

# noqa: F401 — imported for SQLAlchemy metadata registration
from app.compliance.models import ComplianceReportRecord  # Sprint 2
