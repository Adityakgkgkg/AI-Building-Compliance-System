"""
MCRDSE Sprint 1 – Report Service Layer
========================================
``ReportService`` is the HTTP-facing service layer sitting between the FastAPI
router and the ``EvidenceCollector``.

Responsibilities:
- Invoke ``EvidenceCollector.build_bundle()`` with caller-supplied parameters.
- Translate typed domain exceptions into HTTP-serialisable
  ``ModuleErrorDetail`` envelopes so the router can return meaningful HTTP
  status codes without catching bare ``Exception``.
- Optionally persist a completed bundle to the database when ``persist=True``.

This class intentionally holds no business logic and performs no data
transformation — it delegates entirely to ``EvidenceCollector``.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, Tuple, Union

from app.report.evidence_collector import EvidenceCollector
from app.report.exceptions import (
    ClassificationUnavailableError,
    ComplianceUnavailableError,
    EvidenceCollectionError,
    GISUnavailableError,
    ParserUnavailableError,
)
from app.report.models import EvidenceBundleRecord
from app.report.schemas import EvidenceBundle, ModuleErrorDetail
from app.report.utils import utc_now

logger = logging.getLogger("app.report.service")

# Type alias: service returns either a bundle (success) or an error detail
# paired with the recommended HTTP status code.
ServiceResult = Union[EvidenceBundle, Tuple[ModuleErrorDetail, int]]

# HTTP status codes for each module failure class
_HTTP_STATUS_MAP: dict[type, int] = {
    ParserUnavailableError: 503,
    ClassificationUnavailableError: 503,
    GISUnavailableError: 503,
    ComplianceUnavailableError: 503,
    EvidenceCollectionError: 500,
}


class ReportService:
    """
    Service layer exposing a single ``collect_evidence`` operation.

    Usage::

        result = ReportService.collect_evidence(
            ifc_file="plan.ifc",
            lat=12.9250,
            lon=77.5938,
        )
        if isinstance(result, EvidenceBundle):
            # success path
        else:
            error_detail, http_status = result
            # error path

    Persistence::

        ReportService.collect_evidence(..., persist=True, db=session)
    """

    @staticmethod
    def collect_evidence(
        ifc_file: str,
        lat: float,
        lon: float,
        persist: bool = False,
        db: Optional[object] = None,
    ) -> ServiceResult:
        """
        Orchestrate evidence collection and return the bundle or a structured error.

        Parameters
        ----------
        ifc_file:
            Filename of the IFC file to parse.
        lat:
            WGS84 latitude of the building site.
        lon:
            WGS84 longitude of the building site.
        persist:
            When ``True``, a successfully assembled bundle is persisted to the
            database via ``db`` session.  Defaults to ``False`` (Sprint 1).
        db:
            SQLAlchemy ``Session`` instance.  Required when ``persist=True``.

        Returns
        -------
        EvidenceBundle
            On full success — canonical evidence bundle ready for serialisation.
        Tuple[ModuleErrorDetail, int]
            On any upstream module failure — structured error detail and the
            recommended HTTP status code.
        """
        collector = EvidenceCollector()

        try:
            bundle = collector.build_bundle(
                ifc_file=ifc_file,
                lat=lat,
                lon=lon,
            )
        except EvidenceCollectionError as exc:
            error_detail = ModuleErrorDetail(
                error_code=exc.code,
                module=exc.module,
                detail=exc.message,
            )
            http_status = _HTTP_STATUS_MAP.get(type(exc), 500)
            logger.warning(
                "Evidence collection failed | module=%s code=%s status=%d",
                exc.module,
                exc.code,
                http_status,
            )
            return error_detail, http_status

        if persist:
            ReportService._persist_bundle(bundle=bundle, db=db)

        return bundle

    @staticmethod
    def _persist_bundle(bundle: EvidenceBundle, db: Optional[object]) -> None:
        """
        Persist a completed ``EvidenceBundle`` to the database.

        This is an opt-in operation; failures are logged but do not propagate
        so the HTTP response is unaffected.

        Parameters
        ----------
        bundle:
            Fully assembled evidence bundle.
        db:
            SQLAlchemy ``Session`` instance.
        """
        if db is None:
            logger.warning(
                "persist=True but no db session provided; skipping persistence | "
                "report_id=%s",
                bundle.report_id,
            )
            return

        try:
            record = EvidenceBundleRecord(
                report_id=bundle.report_id,
                ifc_file=bundle.building.ifc_file,
                created_at=utc_now(),
                bundle_json=json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False),
                compliance_score=bundle.compliance.score,
                blocking_violations=bundle.compliance.blocking,
                gis_ward=bundle.gis.ward,
                software_version=bundle.software_version,
            )
            db.add(record)  # type: ignore[union-attr]
            db.commit()  # type: ignore[union-attr]
            logger.info(
                "EvidenceBundle persisted | report_id=%s", bundle.report_id
            )
        except Exception as exc:
            logger.error(
                "Failed to persist EvidenceBundle | report_id=%s | error=%s",
                bundle.report_id,
                exc,
            )
            # Do not re-raise — persistence failure must not affect the HTTP response.
