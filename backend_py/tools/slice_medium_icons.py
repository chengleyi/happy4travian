import os, re, json
from PIL import Image

def load_units():
    base = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'troops_t4.6_1x.json'))
    try:
        with open(base, 'r', encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        with open(base, 'r', encoding='utf-8-sig') as f:
            d = json.load(f)
    out = {}
    for t in d.get('tribes', []):
        tid = int(t.get('tribeId'))
        arr = t.get('units') or []
        names = []
        for u in arr:
            n = str(u.get('name') or u.get('code') or '').strip() or 'unit'
            names.append(n)
        out[tid] = names
    return out

def tribe_name_map(tid):
    m = {1:'roman',2:'teutons',3:'gauls',6:'egyptians',7:'huns',8:'spartan'}
    return m.get(int(tid), 'unknown')

def resource_path_for_tid(tid):
    nm = {1:'roman_medium.png',2:'teuton_medium.png',3:'gaul_medium.png',6:'egyptian_medium.png',7:'hun_medium.png',8:'spartan_medium.png'}
    fn = nm.get(int(tid))
    if not fn:
        return None
    p = os.path.abspath(os.path.join(os.getcwd(), 'resource', fn))
    return p if os.path.exists(p) else None

def safe_name(s):
    return re.sub(r'[^A-Za-z0-9_\-]', '_', s)

def slice_image(img, count):
    w, h = img.width, img.height
    if count <= 0:
        return []
    seg = h // count
    out = []
    for i in range(count):
        y0 = i * seg
        y1 = (i+1) * seg if i < count - 1 else h
        out.append(img.crop((0, y0, w, y1)))
    return out

def run():
    units = load_units()
    saved = []
    for tid, names in units.items():
        rp = resource_path_for_tid(tid)
        if not rp:
            continue
        img = Image.open(rp)
        patches = slice_image(img, len(names))
        base = os.path.abspath(os.path.join(os.getcwd(), 'resource', 'icons', f"tribe_{tid}_{tribe_name_map(tid)}"))
        os.makedirs(base, exist_ok=True)
        for i, p in enumerate(patches[:len(names)]):
            nm = safe_name(names[i])
            fn = f"{i+1:02d}_{nm}.png"
            outp = os.path.join(base, fn)
            p.save(outp)
            saved.append(outp)
    print(json.dumps({'saved': saved}, ensure_ascii=False))

if __name__ == '__main__':
    run()