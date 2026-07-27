"""
AI Building Compliance System — IFC Parser Models

In-memory data store for uploaded IFC file records and parse results.

Design note: ParsedFileStore wraps a plain dict so that Sprint 3+
can replace it with a SQLAlchemy-backed implementation without
touching any other module — just swap the dependency in service.py.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from app.parser.schemas import ParseResult


# ── Status Enum ───────────────────────────────────────────────────

class FileStatus(str, Enum):
    """Lifecycle states for an uploaded IFC file."""

    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ERROR = "error"


# ── File Record ───────────────────────────────────────────────────

@dataclass
class IFCFileRecord:
    """
    Metadata record for a single uploaded IFC file.

    Attributes:
        file_id:     UUID4 string identifying this upload.
        filename:    Original filename provided by the client.
        file_path:   Absolute path to the saved file on disk.
        uploaded_at: UTC timestamp of upload.
        status:      Current lifecycle status.
        error_msg:   Set when status == ERROR.
    """

    file_id: str
    filename: str
    file_path: Path
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: FileStatus = FileStatus.UPLOADED
    error_msg: Optional[str] = None


# ── In-Memory Store ───────────────────────────────────────────────

class ParsedFileStore:
    """
    Thread-safe in-memory store for IFCFileRecords and ParseResults.

    This class is designed for easy replacement with a database-backed
    implementation in future sprints. The interface contract is:
        save(record) / get(file_id) -> IFCFileRecord | None
        save_result(file_id, result) / get_result(file_id) -> ParseResult | None

    Thread safety: all mutations are guarded by a reentrant lock.
    """

    def __init__(self) -> None:
        self._records: dict[str, IFCFileRecord] = {}
        self._results: dict[str, ParseResult] = {}
        self._lock = threading.RLock()

    # ── Record operations ─────────────────────────────────────────

    def save(self, record: IFCFileRecord) -> None:
        """Persist a new or updated IFCFileRecord."""
        with self._lock:
            self._records[record.file_id] = record

    def get(self, file_id: str) -> Optional[IFCFileRecord]:
        """Retrieve an IFCFileRecord by file_id; returns None if absent."""
        with self._lock:
            return self._records.get(file_id)

    def update_status(
        self,
        file_id: str,
        status: FileStatus,
        error_msg: Optional[str] = None,
    ) -> None:
        """Update the status (and optional error message) of a record."""
        with self._lock:
            record = self._records.get(file_id)
            if record is not None:
                record.status = status
                record.error_msg = error_msg

    # ── Result operations ─────────────────────────────────────────

    def save_result(self, file_id: str, result: ParseResult) -> None:
        """Persist a ParseResult for the given file_id."""
        with self._lock:
            self._results[file_id] = result

    def get_result(self, file_id: str) -> Optional[ParseResult]:
        """Retrieve a ParseResult by file_id; returns None if not yet parsed."""
        with self._lock:
            return self._results.get(file_id)

    # ── Diagnostics ───────────────────────────────────────────────

    def __len__(self) -> int:
        """Return number of tracked records."""
        with self._lock:
            return len(self._records)

    def __repr__(self) -> str:
        with self._lock:
            return (
                f"ParsedFileStore(records={len(self._records)}, "
                f"results={len(self._results)})"
            )


# ── Module-level singleton ────────────────────────────────────────
# Service layer imports this directly. Replace with a DB-backed store in Sprint 3.
file_store = ParsedFileStore()
