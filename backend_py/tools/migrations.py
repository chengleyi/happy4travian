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
    # 统一字符集为 utf8mb4，避免中文被写入为问号
    try:
        result.update(ensure_utf8mb4_charset())
    except Exception as e:
        result['charset_migration_error'] = str(e)
    return result

def ensure_utf8mb4_charset():
    """将数据库与所有已存在的表转换为 utf8mb4/utf8mb4_unicode_ci"""
    insp = inspect(engine)
    changed = {}
    with engine.begin() as conn:
        # 转数据库字符集（若权限允许）
        conn.execute(text("SELECT database()"))
        try:
            conn.execute(text("ALTER DATABASE CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            changed['database.charset'] = 'utf8mb4'
        except Exception:
            pass
        # 需要转换的表列表
        tables = [
            'alliances','alliance_members','users','servers','tribes',
            'game_accounts','villages','troop_types','troop_counts'
        ]
        for t in tables:
            if insp.has_table(t):
                try:
                    conn.execute(text(f"ALTER TABLE {t} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                    changed[f'{t}.charset'] = 'utf8mb4'
                except Exception:
                    # 尝试逐列修复常见文本列
                    if t == 'alliances':
                        # alliances 特殊处理：确保 name/tag/description 均为 utf8mb4
                        try:
                            conn.execute(text("ALTER TABLE alliances MODIFY COLUMN name VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                            changed['alliances.name'] = 'utf8mb4'
                        except Exception:
                            pass
                        try:
                            conn.execute(text("ALTER TABLE alliances MODIFY COLUMN tag VARCHAR(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                            changed['alliances.tag'] = 'utf8mb4'
                        except Exception:
                            pass
                        try:
                            conn.execute(text("ALTER TABLE alliances MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                            changed['alliances.description'] = 'utf8mb4'
                        except Exception:
                            pass
                    else:
                        try:
                            conn.execute(text(f"ALTER TABLE {t} MODIFY COLUMN name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                        except Exception:
                            pass
                        try:
                            conn.execute(text(f"ALTER TABLE {t} MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                        except Exception:
                            pass
    return changed or {'charset': 'ok'}

if __name__ == '__main__':
    import json
    changes = migrate_missing_columns()
    print(json.dumps({"changes": changes}, ensure_ascii=False))