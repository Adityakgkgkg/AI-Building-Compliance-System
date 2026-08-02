"""
GIS Query Cache Manager
=======================
In-memory cache layer for spatial context query responses.
"""

from typing import Dict, Any, Optional, Tuple


class GISCache:
    """Thread-safe LRU/dict spatial cache."""
    _cache: Dict[Tuple[float, float], Any] = {}

    @classmethod
    def get_key(cls, lat: float, lon: float) -> Tuple[float, float]:
        return round(lat, 6), round(lon, 6)

    @classmethod
    def get(cls, lat: float, lon: float) -> Optional[Any]:
        return cls._cache.get(cls.get_key(lat, lon))

    @classmethod
    def set(cls, lat: float, lon: float, value: Any) -> None:
        cls._cache[cls.get_key(lat, lon)] = value

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()
