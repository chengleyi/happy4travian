import os
import requests

BASE = os.getenv("BASE_URL", "http://localhost:8080/api/v1")

def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    assert r.text == "ok"

def test_end_to_end():
    # servers
    s = requests.post(f"{BASE}/servers", json={"code":"ts1.cn", "region":"cn", "speed":"1x", "startDate": None}).json()
    # tribes
    t = requests.post(f"{BASE}/tribes", json={"code":"roman", "name":"罗马"}).json()

    # seed troop types via API
    requests.post(f"{BASE}/troop-types", json={"tribeId": t["id"], "code": "unit1", "name": "兵1"}).json()
    requests.post(f"{BASE}/troop-types", json={"tribeId": t["id"], "code": "unit2", "name": "兵2"}).json()

    # accounts
    a = requests.post(f"{BASE}/accounts", json={"userId": 1, "serverId": s["id"], "tribeId": t["id"], "inGameName": "tester"}).json()

    # villages
    v = requests.post(f"{BASE}/villages", json={"serverId": s["id"], "gameAccountId": a["id"], "name": "home", "x": 0, "y": 0}).json()

    # alliances
    al = requests.post(f"{BASE}/alliances", json={"serverId": s["id"], "name": "TRAVCO", "tag": "TV", "description": "test", "createdBy": 1}).json()
    m = requests.post(f"{BASE}/alliances/{al['id']}/members", json={"gameAccountId": a["id"], "role": "member"}).json()

    # troop types
    tt = requests.get(f"{BASE}/troop-types", params={"tribeId": t["id"]}).json()
    assert len(tt) >= 2
    type_ids = [tt[0]["id"], tt[1]["id"]]

    # troops upload and aggregate
    requests.post(f"{BASE}/troops/upload", json={"villageId": v["id"], "counts": {str(type_ids[0]): 10, str(type_ids[1]): 20}}).text
    agg = requests.get(f"{BASE}/troops/aggregate", params={"villageId": v["id"]}).json()
    assert agg[str(type_ids[0])] == 10
    assert agg[str(type_ids[1])] == 20

    # parse-upload (simulate html numbers)
    html = "<table><tr><td>5</td><td>15</td></tr></table>"
    parsed = requests.post(f"{BASE}/troops/parse-upload", json={"villageId": v["id"], "html": html}).json()
    assert parsed["written"] is True