"""兵种参数导出为最小 xlsx（手工 XML 版）

无需第三方库，通过构造必要的 XML 并打包 Zip 生成 xlsx 文件。
"""
import os
import json
from datetime import timedelta
from zipfile import ZipFile, ZIP_DEFLATED

CN_TRIBES = {
    1: "罗马", 2: "条顿", 3: "高卢", 4: "自然", 5: "纳塔",
    6: "埃及", 7: "匈奴", 8: "斯巴达", 9: "维京"
}
CN_UNITS = {
    1: ["军团兵","禁卫兵","帝国兵","侦察骑兵","帝国骑兵","凯撒骑兵","攻城槌","投石车","参议员","移民"],
    2: ["棒兵","矛兵","斧兵","侦察兵","圣骑士","条顿骑士","攻城槌","投石车","酋长","移民"],
    3: ["方阵","剑士","探路者","雷霆骑兵","德鲁伊骑士","海都安骑士","攻城槌","投石车","首领","移民"]
}
CN_TYPE = {"i": "步兵", "c": "骑兵"}

def fmt_time(sec):
    """秒转 H:MM:SS 字符串"""
    if not isinstance(sec, (int, float)) or sec <= 0:
        return "0:00:00"
    return str(timedelta(seconds=int(sec)))

HEADERS = [
    "TribeId 部落ID",
    "Tribe(EN) 部落(英文)",
    "部落(中文) Tribe(ZH)",
    "UnitId 兵种ID",
    "Name(EN) 英文名称",
    "名称(中文) Name(ZH)",
    "Type 类型",
    "Off 攻击",
    "Def_i 防御(步)",
    "Def_c 防御(骑)",
    "Speed 速度",
    "Cap 负重",
    "Cost 木 Lumber",
    "Cost 泥 Clay",
    "Cost 铁 Iron",
    "Cost 粮 Crop",
    "Upkeep 维护",
    "TrainTime 训练时间(s)",
    "TrainTimeFmt 训练时间",
    "ResearchTime 研究时间(s)",
    "ResearchTimeFmt 研究时间"
]

def make_cell(col, row, value, is_str=False):
    """构造单元格 XML"""
    addr = f"{col}{row}"
    if is_str:
        safe = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<c r=\"{addr}\" t=\"inlineStr\"><is><t>{safe}</t></is></c>"
    else:
        if value is None:
            return f"<c r=\"{addr}\"/>"
        return f"<c r=\"{addr}\"><v>{value}</v></c>"

def col_letter(idx):
    """将列号转换为 Excel 列字母（1->A）"""
    s = ""
    while idx:
        idx, r = divmod(idx-1, 26)
        s = chr(65+r) + s
    return s

def build_sheet_rows(data):
    """构造工作表行 XML 列表"""
    rows = []
    # Header row
    cells = []
    for i, h in enumerate(HEADERS, 1):
        cells.append(make_cell(col_letter(i), 1, h, True))
    rows.append(f"<row r=\"1\">{''.join(cells)}</row>")
    r = 2
    for tribe in data.get("tribes", []):
        tid = int(tribe.get("tribeId"))
        en_label = tribe.get("tribeLabel") or f"tribe_{tid}"
        cn_label = CN_TRIBES.get(tid, en_label)
        for u in tribe.get("units", []):
            uid = int(u.get("unitId"))
            en_name = u.get("name") or ""
            cn_name_list = CN_UNITS.get(tid, [])
            cn_name = cn_name_list[uid-1] if cn_name_list and uid-1 < len(cn_name_list) else en_name
            row_vals = [
                tid, en_label, cn_label, uid, en_name, cn_name,
                CN_TYPE.get(str(u.get("type")), str(u.get("type"))),
                u.get("off"), u.get("def_i"), u.get("def_c"), u.get("speed"), u.get("cap"),
                (u.get("cost") or [None]*4)[0], (u.get("cost") or [None]*4)[1], (u.get("cost") or [None]*4)[2], (u.get("cost") or [None]*4)[3],
                u.get("cu"), u.get("time"), fmt_time(u.get("time")), u.get("rs_time"), fmt_time(u.get("rs_time"))
            ]
            cells = []
            for i, v in enumerate(row_vals, 1):
                cells.append(make_cell(col_letter(i), r, v, isinstance(v, str)))
            rows.append(f"<row r=\"{r}\">{''.join(cells)}</row>")
            r += 1
    return rows

def export_xlsx(json_path: str, out_path: str):
    """生成最小 xlsx 并返回路径"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sheet_rows = build_sheet_rows(data)
    worksheet_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        "</worksheet>"
    )
    workbook_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"Troops\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )
    workbook_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
        "</Relationships>"
    )
    root_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "</Relationships>"
    )
    styles_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"></styleSheet>"
    )
    content_types = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
        "</Types>"
    )
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook_xml)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/styles.xml", styles_xml)
        z.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return out_path

def main():
    """命令行入口：生成最小 xlsx"""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "troops_t4.6_1x.json"))
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "exports", "troops_t4.6_1x.xlsx"))
    print(export_xlsx(base, out_path))

if __name__ == "__main__":
    main()