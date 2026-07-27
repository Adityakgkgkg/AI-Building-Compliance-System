"""
AI Building Compliance System — Compliance Engine Package

Module 2: Compliance Engine
===========================
Evaluates IFC parser JSON output against BBMP Building Bye-Laws 2003.

Public surface consumed by:
  - The FastAPI router (via this package's router export)
  - Future modules (AI, GIS) via ComplianceReport schema

Components:
  - RuleLoader       — loads rules from JSON files
  - RuleEngine       — evaluates rules against building context
  - ReportGenerator  — assembles the final ComplianceReport
  - ComplianceService — orchestrates the full pipeline

Endpoints (mounted at /api/v1/compliance):
  POST /check                — run compliance check (inline)
  POST /check/{file_id}      — run compliance check (by file_id)
  GET  /report/{file_id}     — retrieve cached report
  GET  /rules                — list all rules
  GET  /rules/{rule_id}      — get single rule detail
"""

from app.compliance.router import router

__all__ = ["router"]
