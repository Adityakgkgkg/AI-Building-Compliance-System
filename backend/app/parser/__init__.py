"""
AI Building Compliance System — IFC Parser Package

Module 1: IFC Parser
====================
Provides IFC file upload, validation, parsing, and data extraction.

Public surface consumed by future modules:
  - ParseResult   — stable JSON contract (building + elements + geometry)
  - ParserService — orchestrates the full pipeline

Endpoints (mounted at /api/v1/parser):
  POST /upload           — validate & save an IFC file, return file_id
  POST /parse/{file_id}  — parse IFC, return full ParseResult
  GET  /building/{file_id} — return BuildingInfo only
  GET  /elements/{file_id} — return ElementCounts only
"""

from app.parser.router import router

__all__ = ["router"]
