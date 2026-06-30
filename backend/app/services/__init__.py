"""
AI Building Compliance System — Business Services

This package will contain service-layer modules in future sprints:
  - Sprint 2: ifc_parser.py  — IFC file parsing and data extraction
  - Sprint 3: compliance.py  — Rule-based compliance checking engine
  - Sprint 4: gis_service.py — GIS context integration
  - Sprint 5: ai_engine.py   — AI/ML recommendation engine

Each service should follow the pattern:

    class ServiceName:
        def __init__(self, db: Session):
            self.db = db

        def process(self, ...) -> ResultSchema:
            ...
"""
