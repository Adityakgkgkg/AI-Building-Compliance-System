"""
MCRDSE Sprint 1 – Domain Exceptions
====================================
Structured exception hierarchy for the Evidence Collection Layer.
Each exception carries a machine-readable code and human-readable context so
callers can respond with precise HTTP semantics without catching bare Exceptions.
"""

from __future__ import annotations


class EvidenceCollectionError(RuntimeError):
    """Base exception for all evidence collection failures."""

    code: str = "EVIDENCE_COLLECTION_ERROR"

    def __init__(self, message: str, module: str = "unknown") -> None:
        super().__init__(message)
        self.message = message
        self.module = module

    def as_dict(self) -> dict:
        return {
            "error_code": self.code,
            "module": self.module,
            "detail": self.message,
        }


class ParserUnavailableError(EvidenceCollectionError):
    """Raised when the IFC Parser module cannot supply building data."""

    code = "PARSER_MODULE_UNAVAILABLE"

    def __init__(self, detail: str = "IFC Parser module is unavailable or returned no data.") -> None:
        super().__init__(message=detail, module="ifc_parser")


class ClassificationUnavailableError(EvidenceCollectionError):
    """Raised when the Building Classification module cannot supply data."""

    code = "CLASSIFICATION_MODULE_UNAVAILABLE"

    def __init__(self, detail: str = "Building Classification module is unavailable or returned no data.") -> None:
        super().__init__(message=detail, module="classification")


class GISUnavailableError(EvidenceCollectionError):
    """Raised when the GIS Context Engine is unavailable or returns invalid data."""

    code = "GIS_MODULE_UNAVAILABLE"

    def __init__(self, detail: str = "GIS Context Engine is unavailable or returned no spatial data.") -> None:
        super().__init__(message=detail, module="gis_context_engine")


class ComplianceUnavailableError(EvidenceCollectionError):
    """Raised when the Compliance Engine cannot supply rule evaluation results."""

    code = "COMPLIANCE_MODULE_UNAVAILABLE"

    def __init__(self, detail: str = "Compliance Engine is unavailable or returned no results.") -> None:
        super().__init__(message=detail, module="compliance_engine")


class BundleAssemblyError(EvidenceCollectionError):
    """Raised when the EvidenceBundle cannot be assembled from collected parts."""

    code = "BUNDLE_ASSEMBLY_ERROR"

    def __init__(self, detail: str = "Failed to assemble EvidenceBundle from collected module outputs.") -> None:
        super().__init__(message=detail, module="evidence_collector")
