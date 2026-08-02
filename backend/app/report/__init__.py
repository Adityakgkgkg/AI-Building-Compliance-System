"""
Module 4 – Municipal Compliance Reporting & Decision Support Engine (MCRDSE)
Sprint 1 – Evidence Collection Layer

Public API of the ``app.report`` package.  Import from here to avoid coupling
to internal sub-module paths.
"""

from app.report.evidence_collector import EvidenceCollector
from app.report.exceptions import (
    BundleAssemblyError,
    ClassificationUnavailableError,
    ComplianceUnavailableError,
    EvidenceCollectionError,
    GISUnavailableError,
    ParserUnavailableError,
)
from app.report.schemas import (
    BuildingEvidence,
    ClassificationEvidence,
    CollectionMetadata,
    ComplianceEvidence,
    DatasetProvenance,
    EvidenceBundle,
    GISEvidence,
    ModuleErrorDetail,
    RuleResult,
)
from app.report.service import ReportService

__all__ = [
    # Canonical schemas
    "EvidenceBundle",
    "BuildingEvidence",
    "ClassificationEvidence",
    "GISEvidence",
    "ComplianceEvidence",
    "RuleResult",
    "DatasetProvenance",
    "CollectionMetadata",
    "ModuleErrorDetail",
    # Orchestrator
    "EvidenceCollector",
    # Service layer
    "ReportService",
    # Exceptions
    "EvidenceCollectionError",
    "ParserUnavailableError",
    "ClassificationUnavailableError",
    "GISUnavailableError",
    "ComplianceUnavailableError",
    "BundleAssemblyError",
]
