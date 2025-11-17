"""抓取 Kirilloid 兵种数据并静态化

从 kirilloid 站点抓取 troops 页面与 units.js，解析出 1.46 版本的 1x 兵种数据并写入 JSON 文件。
"""
import re
import json
import os
from urllib.request import urlopen

BASE_URL = "http://travian.kirilloid.ru"
TROOPS_URL = f"{BASE_URL}/troops.php#s=1.46&tribe=1&s_lvl=1&t_lvl=1&unit=1"
UNITS_JS_URL = f"{BASE_URL}/js/units.js?d"

def fetch(url):
    """获取文本内容（忽略编码错误）"""
    with urlopen(url) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract_names(html):
    """从 HTML 中解析兵种名称二维数组"""
    m = re.search(r"names:\s*\[(.*?)\]\s*;", html, re.S)
    if not m:
        raise RuntimeError("names array not found")
    block = m.group(1)
    arrs = []
    for part in re.findall(r"\[(.*?)\]", block, re.S):
        items = [x.strip() for x in re.findall(r"\"(.*?)\"", part)]
        arrs.append(items)
    return arrs

def extract_tribe_labels(html):
    """解析部落下拉的标签文本列表"""
    sel = re.search(r"<select id=\"tribe\"[\s\S]*?</select>", html)
    if not sel:
        return []
    options = re.findall(r"<option[^>]*>([^<]+)</option>", sel.group(0))
    return options

def _jsonize(js_text):
    """将部分 JS 对象文本转换为 JSON 格式便于解析"""
    j = js_text
    j = re.sub(r"'(.*?)'", lambda m: json.dumps(m.group(1)), j)
    j = re.sub(r"([\{,\s])(\w+):", r"\1"\2":", j)
    return j

def extract_units_base(js_text):
    """解析基础 units 数组"""
    m = re.search(r"var\s+units\s*=\s*\[(.*?)]\s*;", js_text, re.S)
    if not m:
        raise RuntimeError("units base array not found")
    j = _jsonize("[" + m.group(1) + "]")
    return json.loads(j)

def extract_t4_overrides(js_text):
    """解析 t4 覆盖数组（可为空）"""
    m = re.search(r"var\s+t4\s*=\s*extend\(units,\s*\[(.*?)]\s*\)\s*;", js_text, re.S)
    if not m:
        return None
    j = _jsonize("[" + m.group(1) + "]")
    return json.loads(j)

def deep_extend(proto, mixin):
    """按索引深度合并 t4 覆盖到基础数据"""
    if mixin is None:
        return proto
    out = []
    for i, tribe in enumerate(proto):
        t_override = mixin[i] if i < len(mixin) else None
        tribe_out = []
        for u_idx, unit in enumerate(tribe):
            u_override = None
            if isinstance(t_override, list) and u_idx < len(t_override):
                u_override = t_override[u_idx]
            merged = dict(unit)
            if isinstance(u_override, dict):
                for k, v in u_override.items():
                    merged[k] = v
            tribe_out.append(merged)
        out.append(tribe_out)
    return out

def build_t46_1x():
    """构建 1.46 版本 1x 兵种数据结构"""
    html = fetch(TROOPS_URL)
    log("html fetched")
    names = extract_names(html)
    log("names extracted")
    tribe_labels = extract_tribe_labels(html)
    log("tribe labels extracted")
    js = fetch(UNITS_JS_URL)
    log("units.js fetched")
    base = extract_units_base(js)
    log("base parsed")
    t4_over = extract_t4_overrides(js)
    log("t4 overrides parsed")
    t4 = deep_extend(base, t4_over)
    log("deep extended")
    for r, tribe in enumerate(t4):
        for u, unit in enumerate(tribe):
            unit["tribeId"] = r + 1
            unit["unitId"] = u + 1
            unit["name"] = names[r][u] if r < len(names) and u < len(names[r]) else ""
    data = {
        "version": "1.46",
        "speed": "1x",
        "tribes": []
    }
    for r, tribe in enumerate(t4):
        label = tribe_labels[r] if r < len(tribe_labels) else f"tribe_{r+1}"
        data["tribes"].append({
            "tribeId": r + 1,
            "tribeLabel": label,
            "units": tribe
        })
    return data

def main():
    """运行抓取并写入到 data/troops_t4.6_1x.json"""
    try:
        data = build_t46_1x()
        out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.abspath(os.path.join(out_dir, "troops_t4.6_1x.json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print(out_path)
    except Exception as e:
        log(e)
        print(str(e))
        raise

if __name__ == "__main__":
    main()
def log(msg):
    """简单写入调试日志到 data/scrape_debug.txt（忽略错误）"""
    p = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "scrape_debug.txt"))
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass