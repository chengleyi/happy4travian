import sys
import time
import json
import requests

BASES = [
    "http://47.243.146.179:8080",
    "http://47.243.146.179",
    "https://47.243.146.179",
    "https://happy4travian.com",
    "https://www.happy4travian.com",
    "http://127.0.0.1:8080",
]

ENDPOINTS = [
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/healthz"),
    ("GET", "/api/v1/db/ping"),
    ("GET", "/api/v1/troops_params"),
    ("GET", "/api/v1/troops/params"),
    ("GET", "/api/v1/users"),
    ("GET", "/api/v1/servers"),
    ("GET", "/api/v1/tribes"),
    ("GET", "/api/v1/accounts"),
    ("GET", "/api/v1/villages"),
    ("GET", "/api/v1/alliances"),
]

def check_base(session, base):
    try:
        r = session.get(base + "/api/v1/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def req(session, method, url):
    f = getattr(session, method.lower())
    return f(url, timeout=8)

def main():
    session = requests.Session()
    session.trust_env = False
    all_results = []
    bases_checked = []
    for base in BASES:
        reachable = check_base(session, base)
        bases_checked.append({"base": base, "reachable": bool(reachable)})
        results = []
        for method, path in ENDPOINTS:
            url = base + path
            try:
                r = req(session, method, url)
                ok = r.status_code == 200 and isinstance(r.json(), dict) and r.json().get("success") is True
                body = r.text
                if len(body) > 400:
                    body = body[:400] + "..."
                results.append({"method": method, "path": path, "status": r.status_code, "ok": bool(ok), "body": body})
            except Exception as e:
                results.append({"method": method, "path": path, "status": None, "ok": False, "error": str(e)})
        all_results.append({"base": base, "results": results})
    # alliances detail checks
    try:
        r = session.get(BASES[0] + "/api/v1/alliances", timeout=8)
        data = r.json().get("data") if r.status_code == 200 else None
        if isinstance(data, list) and data:
            aid = data[0].get("id")
            if aid:
                for path in [f"/api/v1/alliances/{aid}", f"/api/v1/alliances/{aid}/members"]:
                    try:
                        rr = session.get(BASES[0] + path, timeout=8)
                        ok = rr.status_code == 200 and isinstance(rr.json(), dict) and rr.json().get("success") is True
                        body = rr.text
                        if len(body) > 400:
                            body = body[:400] + "..."
                        all_results.append({"base": BASES[0], "results": [{"method": "GET", "path": path, "status": rr.status_code, "ok": bool(ok), "body": body}]})
                    except Exception as e:
                        all_results.append({"base": BASES[0], "results": [{"method": "GET", "path": path, "status": None, "ok": False, "error": str(e)}]})
    except Exception:
        pass
    flat = [x for group in all_results for x in group.get("results", [])]
    output = {
        "bases": bases_checked,
        "summary": {
            "total": len(flat),
            "passed": sum(1 for x in flat if x.get("ok")),
            "failed": sum(1 for x in flat if not x.get("ok")),
        },
        "details": all_results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()