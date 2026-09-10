"""
JSON-based storage layer for transport cards system.
Designed to be easily replaceable with SQL (MySQL/PostgreSQL) later.
"""
import json
import os
import uuid
import time
from datetime import datetime
from pathlib import Path

# Import logging for operations
try:
    from app.logger import log_db_query, log_error, log_performance_metric
    LOGGING_ENABLED = True
except ImportError:
    LOGGING_ENABLED = False

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _get_path(name):
    return DATA_DIR / f"{name}.json"


def load_all(name):
    path = _get_path(name)
    if not path.exists():
        return []
    start_time = time.time()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        duration_ms = (time.time() - start_time) * 1000
        if LOGGING_ENABLED:
            log_db_query(name, "SELECT", duration_ms)
        return data
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"load_all({name})", {"path": str(path)})
        raise


def save_all(name, data):
    path = _get_path(name)
    start_time = time.time()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        duration_ms = (time.time() - start_time) * 1000
        if LOGGING_ENABLED:
            log_db_query(name, "SAVE", duration_ms)
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"save_all({name})", {"path": str(path)})
        raise


def find_one(name, predicate):
    start_time = time.time()
    try:
        result = None
        for item in load_all(name):
            if predicate(item):
                result = item
                break
        duration_ms = (time.time() - start_time) * 1000
        if LOGGING_ENABLED:
            log_db_query(name, "FIND_ONE", duration_ms)
        return result
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"find_one({name})", {})
        raise


def find_many(name, predicate):
    start_time = time.time()
    try:
        result = [item for item in load_all(name) if predicate(item)]
        duration_ms = (time.time() - start_time) * 1000
        if LOGGING_ENABLED:
            log_db_query(name, "FIND_MANY", duration_ms)
        return result
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"find_many({name})", {})
        raise


def insert(name, item):
    data = load_all(name)
    if "id" not in item or not item["id"]:
        item["id"] = str(uuid.uuid4())
    item["created_at"] = datetime.now().isoformat()
    data.append(item)
    save_all(name, data)
    if LOGGING_ENABLED:
        log_db_query(name, "INSERT", None)
    return item


def update(name, predicate, updates):
    data = load_all(name)
    start_time = time.time()
    try:
        for item in data:
            if predicate(item):
                item.update(updates)
                item["updated_at"] = datetime.now().isoformat()
                save_all(name, data)
                duration_ms = (time.time() - start_time) * 1000
                if LOGGING_ENABLED:
                    log_db_query(name, "UPDATE", duration_ms)
                return item
        return None
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"update({name})", {})
        raise


def delete(name, predicate):
    data = load_all(name)
    start_time = time.time()
    try:
        new_data = [item for item in data if not predicate(item)]
        save_all(name, new_data)
        duration_ms = (time.time() - start_time) * 1000
        if LOGGING_ENABLED:
            log_db_query(name, "DELETE", duration_ms)
    except Exception as e:
        if LOGGING_ENABLED:
            log_error(e, f"delete({name})", {})
        raise


def get_next_number(prefix, name="counters"):
    """Get next sequential document number."""
    counters = load_all(name)
    counter = next((c for c in counters if c.get("prefix") == prefix), None)
    if counter is None:
        counter = {"prefix": prefix, "value": 1}
        counters.append(counter)
    else:
        counter["value"] += 1
    save_all(name, counters)
    if LOGGING_ENABLED:
        log_db_query(name, "GET_NEXT_NUMBER", None)
    return f"{prefix}-{counter['value']:03d}"


# Initialize default data
def init_defaults():
    # Default admin user
    employees = load_all("employees")
    if not employees:
        insert("employees", {
            "id": str(uuid.uuid4()),
            "full_name": "Администратор",
            "login": "admin",
            "password": "admin",  # In production, use hashed passwords
            "roles": ["admin"],
            "permissions": {}
        })

    # Default constants
    constants = load_all("constants")
    if not constants:
        insert("constants", {
            "id": str(uuid.uuid4()),
            "organization_name": "ООО Транспортные Карты"
        })


init_defaults()
