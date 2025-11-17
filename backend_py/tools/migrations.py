"""简单的列迁移脚本

检测并为 `alliances` 与 `alliance_members` 补充缺失列，使用原生 SQL 执行。
"""
from sqlalchemy import text
from sqlalchemy import inspect
from db import engine

def ensure_alliances_columns():
    """确保 `alliances` 表存在并包含 `created_at` 列"""
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
    """确保 `alliance_members` 表存在并包含必要列"""
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
    """执行所有迁移步骤并返回变更摘要"""
    result = {}
    result.update(ensure_alliances_columns())
    result.update(ensure_alliance_members_columns())
    return result

if __name__ == '__main__':
    import json
    changes = migrate_missing_columns()
    print(json.dumps({"changes": changes}, ensure_ascii=False))