"""
AI Building Compliance System — Utility Helpers
"""

from datetime import datetime, timezone


def get_upload_time() -> datetime:
    """Return the current UTC timestamp for upload records."""
    return datetime.now(timezone.utc)


def get_file_extension(filename: str) -> str:
    """Extract and normalize the file extension (lowercase, with dot)."""
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def format_file_size(size_bytes: int) -> str:
    """Format byte count into a human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
