"""
AGL Security â€” MongoDB Database Layer
Ø·Ø¨Ù‚Ø© Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª â€” MongoDB

Provides the same logical interface as the SQLAlchemy layer but stores
everything in MongoDB. Falls back gracefully when MongoDB is unreachable.

Collections:
  - users       (email index, unique)
  - api_keys    (key index, unique)
  - scans       (user_id + created_at compound index)

Environment variables:
  AGL_MONGO_URI  â€” connection string  (default: mongodb://localhost:27017)
  AGL_MONGO_DB   â€” database name      (default: agl_security)
"""

import os
import uuid
import datetime
from typing import Optional, List, Dict, Any

from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    DuplicateKeyError,
)

# â”€â”€ Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MONGO_URI = os.environ.get("AGL_MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("AGL_MONGO_DB", "agl_security")

# â”€â”€ Singleton Connection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_client: Optional[MongoClient] = None
_db = None
_available: Optional[bool] = None


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  Connection Management
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def get_mongo_client() -> Optional[MongoClient]:
    """Return a singleton MongoClient, or None if unreachable."""
    global _client, _db, _available
    if _client is not None:
        return _client
    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[MONGO_DB_NAME]
        _available = True
        return _client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"âš ï¸  MongoDB unavailable: {e}")
        _available = False
        return None


def get_mongo_db():
    """Return the MongoDB database object."""
    global _db
    if _db is not None:
        return _db
    client = get_mongo_client()
    if client:
        _db = client[MONGO_DB_NAME]
    return _db


def is_mongo_available() -> bool:
    """Check if MongoDB is reachable."""
    global _available
    if _available is not None:
        return _available
    get_mongo_client()
    return _available or False


def init_mongo_db():
    """Create indexes and initialize MongoDB collections."""
    db = get_mongo_db()
    if db is None:
        print("âš ï¸  Skipping MongoDB init â€” not available")
        return False

    # Users collection
    db.users.create_index("email", unique=True)
    db.users.create_index("id", unique=True)

    # API Keys collection
    db.api_keys.create_index("key", unique=True)
    db.api_keys.create_index("id", unique=True)
    db.api_keys.create_index("user_id")

    # Scans collection
    db.scans.create_index("id", unique=True)
    db.scans.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.scans.create_index("status")
    db.scans.create_index("created_at")

    print(f"ðŸƒ MongoDB initialized: {MONGO_DB_NAME}")
    return True


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  Document Wrapper â€” attribute access like SQLAlchemy models
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class MongoDoc:
    """
    Wraps a MongoDB document dict to provide attribute-style access
    (doc.field) just like SQLAlchemy ORM models, keeping route code
    compatible.
    """

    _collection_name: str = ""

    def __init__(self, data: Dict[str, Any]):
        # Use object.__setattr__ to avoid recursion
        object.__setattr__(self, "_data", dict(data))

    def __getattr__(self, key: str):
        data = object.__getattribute__(self, "_data")
        if key in data:
            return data[key]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{key}'")

    def __setattr__(self, key: str, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self._data)
        d.pop("_id", None)
        return d

    def __repr__(self):
        return f"<{type(self).__name__} id={self._data.get('id', '?')}>"


class MongoUser(MongoDoc):
    _collection_name = "users"


class MongoAPIKey(MongoDoc):
    _collection_name = "api_keys"


class MongoScan(MongoDoc):
    _collection_name = "scans"

    @property
    def result(self):
        """Return result_json as result for backward compat."""
        return self._data.get("result_json")


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  Default Document Shapes
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

_DEFAULT_USER = {
    "id": "",
    "email": "",
    "username": "",
    "hashed_pw": "",
    "is_active": True,
    "is_admin": False,
    "created_at": None,
    "last_login": None,
}

_DEFAULT_SCAN = {
    "id": "",
    "user_id": "",
    "target_name": "",
    "target_type": "file",
    "scan_mode": "deep",
    "status": "pending",
    "progress": 0,
    "current_layer": "",
    "total_findings": 0,
    "critical_count": 0,
    "high_count": 0,
    "medium_count": 0,
    "low_count": 0,
    "security_score": 0.0,
    "heikal_xi": None,
    "heikal_wave": None,
    "heikal_tunnel": None,
    "heikal_holo": None,
    "heikal_resonance": None,
    "result_json": None,
    "total_attacks": 0,
    "profitable_attacks": 0,
    "max_profit_usd": 0.0,
    "created_at": None,
    "started_at": None,
    "completed_at": None,
    "duration_sec": 0.0,
    "error_message": None,
}

_DEFAULT_API_KEY = {
    "id": "",
    "key": "",
    "label": "default",
    "user_id": "",
    "is_active": True,
    "created_at": None,
    "last_used": None,
}


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  User CRUD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def create_user(
    email: str, username: str, hashed_pw: str, is_admin: bool = False
) -> Optional[MongoUser]:
    """Create a new user. Returns MongoUser or None on duplicate."""
    db = get_mongo_db()
    if db is None:
        return None
    doc = {**_DEFAULT_USER}
    doc.update(
        {
            "id": _uuid(),
            "email": email,
            "username": username,
            "hashed_pw": hashed_pw,
            "is_admin": is_admin,
            "created_at": _now(),
        }
    )
    try:
        db.users.insert_one(doc)
        return MongoUser(doc)
    except DuplicateKeyError:
        return None


def get_user_by_email(email: str) -> Optional[MongoUser]:
    db = get_mongo_db()
    if db is None:
        return None
    doc = db.users.find_one({"email": email})
    return MongoUser(doc) if doc else None


def get_user_by_id(user_id: str) -> Optional[MongoUser]:
    db = get_mongo_db()
    if db is None:
        return None
    doc = db.users.find_one({"id": user_id})
    return MongoUser(doc) if doc else None


def update_user(user_id: str, **fields) -> bool:
    db = get_mongo_db()
    if db is None:
        return False
    result = db.users.update_one({"id": user_id}, {"$set": fields})
    return result.modified_count > 0


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  API Key CRUD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def create_api_key(
    user_id: str, key: str, label: str = "default"
) -> Optional[MongoAPIKey]:
    db = get_mongo_db()
    if db is None:
        return None
    doc = {**_DEFAULT_API_KEY}
    doc.update(
        {
            "id": _uuid(),
            "key": key,
            "label": label,
            "user_id": user_id,
            "created_at": _now(),
        }
    )
    try:
        db.api_keys.insert_one(doc)
        return MongoAPIKey(doc)
    except DuplicateKeyError:
        return None


def get_api_key(key: str) -> Optional[MongoAPIKey]:
    db = get_mongo_db()
    if db is None:
        return None
    doc = db.api_keys.find_one({"key": key, "is_active": True})
    return MongoAPIKey(doc) if doc else None


def list_api_keys(user_id: str) -> List[MongoAPIKey]:
    db = get_mongo_db()
    if db is None:
        return []
    return [MongoAPIKey(d) for d in db.api_keys.find({"user_id": user_id})]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  Scan CRUD
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def create_scan(
    user_id: str,
    target_name: str,
    target_type: str = "file",
    scan_mode: str = "deep",
    **extra,
) -> Optional[MongoScan]:
    """Create a new scan document."""
    db = get_mongo_db()
    if db is None:
        return None
    doc = {**_DEFAULT_SCAN}
    doc.update(
        {
            "id": _uuid(),
            "user_id": user_id,
            "target_name": target_name,
            "target_type": target_type,
            "scan_mode": scan_mode,
            "created_at": _now(),
        }
    )
    doc.update(extra)
    db.scans.insert_one(doc)
    return MongoScan(doc)


def get_scan(scan_id: str, user_id: Optional[str] = None) -> Optional[MongoScan]:
    """Get a scan by ID, optionally restricted to a user."""
    db = get_mongo_db()
    if db is None:
        return None
    query = {"id": scan_id}
    if user_id:
        query["user_id"] = user_id
    doc = db.scans.find_one(query)
    return MongoScan(doc) if doc else None


def update_scan(scan_id: str, **fields) -> bool:
    """Update scan fields."""
    db = get_mongo_db()
    if db is None:
        return False
    # Convert any non-serializable values
    clean = {}
    for k, v in fields.items():
        if isinstance(v, datetime.datetime):
            clean[k] = v
        elif isinstance(v, (str, int, float, bool, list, dict, type(None))):
            clean[k] = v
        else:
            clean[k] = str(v)
    result = db.scans.update_one({"id": scan_id}, {"$set": clean})
    return result.modified_count > 0


def list_scans(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
) -> List[MongoScan]:
    """List scans for a user, newest first."""
    db = get_mongo_db()
    if db is None:
        return []
    query: Dict[str, Any] = {"user_id": user_id}
    if status:
        query["status"] = status
    cursor = (
        db.scans.find(query).sort("created_at", DESCENDING).skip(offset).limit(limit)
    )
    return [MongoScan(d) for d in cursor]


def count_scans(user_id: str, status: Optional[str] = None) -> int:
    db = get_mongo_db()
    if db is None:
        return 0
    query: Dict[str, Any] = {"user_id": user_id}
    if status:
        query["status"] = status
    return db.scans.count_documents(query)


def delete_scan(scan_id: str, user_id: Optional[str] = None) -> bool:
    db = get_mongo_db()
    if db is None:
        return False
    query = {"id": scan_id}
    if user_id:
        query["user_id"] = user_id
    result = db.scans.delete_one(query)
    return result.deleted_count > 0


def get_user_stats(user_id: str) -> Dict[str, Any]:
    """Aggregate statistics for a user's scans."""
    db = get_mongo_db()
    if db is None:
        return {}

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_scans": {"$sum": 1},
                "completed_scans": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
                "total_findings": {"$sum": "$total_findings"},
                "total_critical": {"$sum": "$critical_count"},
                "total_high": {"$sum": "$high_count"},
                "total_medium": {"$sum": "$medium_count"},
                "total_low": {"$sum": "$low_count"},
                "average_score": {"$avg": "$security_score"},
            }
        },
    ]

    results = list(db.scans.aggregate(pipeline))
    if not results:
        return {
            "total_scans": 0,
            "completed_scans": 0,
            "total_findings": 0,
            "total_critical": 0,
            "total_high": 0,
            "total_medium": 0,
            "total_low": 0,
            "average_score": 0,
        }

    stats = results[0]
    stats.pop("_id", None)
    stats["average_score"] = round(stats.get("average_score", 0) or 0, 1)
    return stats


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  Migration helper: SQLite â†’ MongoDB
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


def migrate_from_sqlite():
    """
    One-time migration: copies all SQLite data to MongoDB.
    Safe to run multiple times (uses upsert).
    """
    try:
        from .database import (
            SessionLocal,
            User as SQLUser,
            Scan as SQLScan,
            APIKey as SQLKey,
        )
    except Exception as e:
        print(f"âš ï¸  Cannot import SQLite models: {e}")
        return

    db = get_mongo_db()
    if db is None:
        print("âš ï¸  MongoDB not available for migration")
        return

    session = SessionLocal()
    try:
        # Migrate users
        for u in session.query(SQLUser).all():
            doc = {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "hashed_pw": u.hashed_pw,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "created_at": u.created_at,
                "last_login": u.last_login,
            }
            db.users.replace_one({"id": u.id}, doc, upsert=True)

        # Migrate API keys
        for k in session.query(SQLKey).all():
            doc = {
                "id": k.id,
                "key": k.key,
                "label": k.label,
                "user_id": k.user_id,
                "is_active": k.is_active,
                "created_at": k.created_at,
                "last_used": k.last_used,
            }
            db.api_keys.replace_one({"id": k.id}, doc, upsert=True)

        # Migrate scans
        for s in session.query(SQLScan).all():
            doc = {
                "id": s.id,
                "user_id": s.user_id,
                "target_name": s.target_name,
                "target_type": s.target_type,
                "scan_mode": s.scan_mode,
                "status": s.status,
                "progress": s.progress,
                "current_layer": s.current_layer or "",
                "total_findings": s.total_findings,
                "critical_count": s.critical_count,
                "high_count": s.high_count,
                "medium_count": s.medium_count,
                "low_count": s.low_count,
                "security_score": s.security_score,
                "heikal_xi": s.heikal_xi,
                "heikal_wave": s.heikal_wave,
                "heikal_tunnel": s.heikal_tunnel,
                "heikal_holo": s.heikal_holo,
                "heikal_resonance": s.heikal_resonance,
                "result_json": s.result_json,
                "total_attacks": s.total_attacks,
                "profitable_attacks": s.profitable_attacks,
                "max_profit_usd": s.max_profit_usd,
                "created_at": s.created_at,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "duration_sec": s.duration_sec,
                "error_message": s.error_message,
            }
            db.scans.replace_one({"id": s.id}, doc, upsert=True)

        user_count = db.users.count_documents({})
        scan_count = db.scans.count_documents({})
        print(f"âœ… Migration complete: {user_count} users, {scan_count} scans")

    finally:
        session.close()
