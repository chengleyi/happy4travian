from sqlalchemy import text
from sqlalchemy import inspect
from db import engine

def ensure_alliances_columns():
    insp = inspect(engine)
    if not insp.has_table('alliances'):
        return {"alliances": "table_missing"}
    cols = {c['name'] for c in insp.get_columns('alliances')}
    changed = {}
    with engine.begin() as conn:
        if 'created_at' not in cols:
            conn.execute(text("ALTER TABLE alliances ADD COLUMN created_at DATETIME NULL"))
            changed['alliances.created_at'] = 'added'
    return changed or {"alliances": "ok"}

def ensure_alliance_members_columns():
    insp = inspect(engine)
    if not insp.has_table('alliance_members'):
        return {"alliance_members": "table_missing"}
    cols = {c['name'] for c in insp.get_columns('alliance_members')}
    changed = {}
    with engine.begin() as conn:
        if 'joined_at' not in cols:
            conn.execute(text("ALTER TABLE alliance_members ADD COLUMN joined_at DATETIME NULL"))
            changed['alliance_members.joined_at'] = 'added'
        if 'role' not in cols:
            conn.execute(text("ALTER TABLE alliance_members ADD COLUMN role VARCHAR(32) NULL"))
            changed['alliance_members.role'] = 'added'
        if 'join_status' not in cols:
            conn.execute(text("ALTER TABLE alliance_members ADD COLUMN join_status VARCHAR(32) NULL"))
            changed['alliance_members.join_status'] = 'added'
    return changed or {"alliance_members": "ok"}

def migrate_missing_columns():
    result = {}
    result.update(ensure_alliances_columns())
    result.update(ensure_alliance_members_columns())
    return result