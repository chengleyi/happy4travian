"""多倍速兵种参数导出（openpyxl）

将 1x 基础数据按多倍速（1,2,3,5,10）生成多个工作表，并套用中文映射。
"""
import os
import json
from datetime import timedelta
from openpyxl import Workbook

SPD_MAP = {1:1, 2:2, 3:2, 5:2, 10:4}
SPEEDS = [1,2,3,5,10]

def fmt_time(sec):
    """秒转 H:MM:SS 字符串"""
    if not isinstance(sec, (int, float)) or sec <= 0:
        return "0:00:00"
    return str(timedelta(seconds=int(sec)))

def load_json(p):
    """容错读取 JSON（utf-8 与 utf-8-sig）"""
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(p, "r", encoding="utf-8-sig") as f:
            return json.load(f)

def build_rows(base, cn_map, k):
    """构建指定倍速 k 的表格行"""
    rows = []
    headers = cn_map["headers"]
    rows.append(headers)
    spd_factor = SPD_MAP.get(k, 1)
    for tribe in base.get("tribes", []):
        tid = int(tribe.get("tribeId"))
        en_label = tribe.get("tribeLabel") or f"tribe_{tid}"
        cn_label = cn_map.get("tribes", {}).get(str(tid), en_label)
        units_cn = cn_map.get("units", {}).get(str(tid), [])
        for u in tribe.get("units", []):
            uid = int(u.get("unitId"))
            en_name = u.get("name") or ""
            cn_name = units_cn[uid-1] if units_cn and uid-1 < len(units_cn) else en_name
            speed_adj = int(round((u.get("speed") or 0) * spd_factor))
            time_adj = int(round((u.get("time") or 0) / k))
            rs_adj = int(round((u.get("rs_time") or 0) / k))
            cost = u.get("cost") or [None, None, None, None]
            ttype = "骑兵" if u.get("type") == "c" else "步兵"
            row = [
                base.get("version"), f"{k}x", tid, en_label, cn_label,
                uid, en_name, cn_name, ttype,
                u.get("off"), u.get("def_i"), u.get("def_c"), speed_adj, u.get("cap"),
                cost[0], cost[1], cost[2], cost[3], u.get("cu"),
                time_adj, fmt_time(time_adj), rs_adj, fmt_time(rs_adj)
            ]
            rows.append(row)
    return rows

def export_multi(base_path, cn_path, out_path):
    """导出多工作表 xlsx 并返回路径"""
    base = load_json(base_path)
    cn = load_json(cn_path)
    wb = Workbook()
    # build each sheet
    first = True
    for k in SPEEDS:
        rows = build_rows(base, cn, k)
        if first:
            ws = wb.active
            ws.title = f"{k}x"
            first = False
        else:
            ws = wb.create_sheet(f"{k}x")
        for r in rows:
            ws.append(r)
    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)
    wb.save(out_path)
    return out_path

def main():
    """命令行入口：按默认路径生成多倍速 xlsx"""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "troops_t4.6_1x.json"))
    cn = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cn_map.json"))
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "exports", "troops_multi.xlsx"))
    print(export_multi(base, cn, out_path))

if __name__ == "__main__":
    main()