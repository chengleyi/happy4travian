import os
import requests
import time
import random

BASE = os.getenv("BASE_URL", "http://localhost:8080/api/v1")

def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.text == "ok"

def test_end_to_end():
    suffix = str(int(time.time())) + str(random.randint(100,999))
    short = str(random.randint(1000,9999))
    # servers
    rs = requests.post(f"{BASE}/servers", json={"code": f"ts-ci-{suffix}", "region":"cn", "speed":"1x", "startDate": None})
    assert rs.status_code == 200
    s = rs.json()
    # users
    ru = requests.post(f"{BASE}/users", json={"nickname": f"ci-{short}"})
    assert ru.status_code == 200
    user = ru.json()

    # tribes
    rt = requests.post(f"{BASE}/tribes", json={"code": f"roman-ci-{short}", "name":"罗马"})
    assert rt.status_code == 200
    t = rt.json()

    # seed troop types via API
    rtt1 = requests.post(f"{BASE}/troop-types", json={"tribeId": t["id"], "code": "unit1", "name": "兵1"})
    rtt2 = requests.post(f"{BASE}/troop-types", json={"tribeId": t["id"], "code": "unit2", "name": "兵2"})
    assert rtt1.status_code == 200 and rtt2.status_code == 200

    # accounts
    ra = requests.post(f"{BASE}/accounts", json={"userId": user["id"], "serverId": s["id"], "tribeId": t["id"], "inGameName": f"tester-ci-{suffix}"})
    assert ra.status_code == 200
    a = ra.json()

    # villages
    rv = requests.post(f"{BASE}/villages", json={"serverId": s["id"], "gameAccountId": a["id"], "name": "home", "x": random.randint(1, 1000), "y": random.randint(1, 1000)})
    assert rv.status_code == 200
    v = rv.json()

    # alliances
    ral = requests.post(f"{BASE}/alliances", json={"serverId": s["id"], "name": "TRAVCO", "tag": f"TV{short}", "description": "test", "createdBy": user["id"]})
    assert ral.status_code == 200
    al = ral.json()
    rm = requests.post(f"{BASE}/alliances/{al['id']}/members", json={"gameAccountId": a["id"], "role": "member"})
    assert rm.status_code == 200

    # troop types
    tt = requests.get(f"{BASE}/troop-types", params={"tribeId": t["id"]}).json()
    type_ids = [tt[0]["id"], tt[1]["id"]]

    # troops upload and aggregate
    ru = requests.post(f"{BASE}/troops/upload", json={"villageId": v["id"], "counts": {str(type_ids[0]): 10, str(type_ids[1]): 20}})
    assert ru.status_code == 200
    _ = requests.get(f"{BASE}/troops/aggregate", params={"villageId": v["id"]}).json()

    # parse-upload (simulate html numbers)
    html = "<table><tr><td>5</td><td>15</td></tr></table>"
    rpu = requests.post(f"{BASE}/troops/parse-upload", json={"villageId": v["id"], "html": html})
    assert rpu.status_code == 200