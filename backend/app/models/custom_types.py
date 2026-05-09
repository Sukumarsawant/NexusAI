import json
from typing import List, Optional
from sqlalchemy import TypeDecorator, String, Text
from app.core.config import settings

try:
    from pgvector.sqlalchemy import Vector as PgVector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class SafeVector(TypeDecorator):
    """
    Cross-platform Vector type.
    Uses pgvector.sqlalchemy.Vector on PostgreSQL,
    and falls back to JSON-serialized Text on SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 768):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVECTOR_AVAILABLE:
            return value
        # SQLite or other: serialize list to JSON string
        return json.dumps(value)

    def process_result_value(self, value, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return None
        # In case pgvector returns numpy array
        if hasattr(value, "tolist"):
            return value.tolist()
        return value
