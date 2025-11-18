import os
import time
import json
import requests

BASE = os.getenv("BASE_URL", "http://47.99.88.168:8080/api/v1")

def post(path, payload):
    r = requests.post(BASE + path, json=payload)
    return r.status_code, r.json()

def put(path, payload):
    r = requests.put(BASE + path, json=payload)
    return r.status_code, r.json()

def get(path):
    r = requests.get(BASE + path)
    return r.status_code, r.json()

def main():
    ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    sc, u = post("/users", {"nickname": "PyReqUser-" + ts})
    print("users", sc, json.dumps(u, ensure_ascii=False))
    uid = u.get("data", {}).get("id")

    sc, s = post("/servers", {"code": "com-pyreq-" + ts, "region": "CN", "speed": "x1", "startDate": "2025-11-20"})
    print("servers", sc, json.dumps(s, ensure_ascii=False))
    sid = s.get("data", {}).get("id")

    sc, t = post("/tribes", {"code": "PYROM-" + ts, "name": "Py Romans"})
    print("tribes", sc, json.dumps(t, ensure_ascii=False))
    tid = t.get("data", {}).get("id")

    sc, a = post("/accounts", {"userId": uid, "serverId": sid, "tribeId": tid, "inGameName": "PyAcc-" + ts})
    print("accounts", sc, json.dumps(a, ensure_ascii=False))
    aid = a.get("data", {}).get("id")

    sc, v = post("/villages", {"serverId": sid, "gameAccountId": aid, "name": "PyVillage-" + ts, "x": 110, "y": -50})
    print("villages", sc, json.dumps(v, ensure_ascii=False))

    sc, al = post("/alliances", {"serverId": sid, "name": "H4T-Py-" + ts, "tag": "HP", "description": "中文演示", "createdBy": uid})
    print("alliances", sc, json.dumps(al, ensure_ascii=False))
    alid = al.get("data", {}).get("id")
    if alid:
        sc, alget = get("/alliances/" + str(alid))
        print("alliances_get", sc, json.dumps(alget, ensure_ascii=False))

    sc, bad = get("/alliances?serverId=abc")
    print("alliances_bad", sc, json.dumps(bad, ensure_ascii=False))

if __name__ == "__main__":
    main()