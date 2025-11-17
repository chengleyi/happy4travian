import os
import json
from datetime import date
from sqlalchemy import select
from db import engine, SessionLocal, Base
from models import User, Server, Tribe, GameAccount, Village, Alliance, AllianceMember, TroopType

def ensure_tables():
    Base.metadata.create_all(engine)

def seed_tribes(db):
    data = [("ROM","Romans"),("TEU","Teutons"),("GAL","Gauls"),("NAT","Natars"),("EGY","Egyptians"),("HUN","Huns"),("SPA","Spartans"),("VIK","Vikings")]
    for code,name in data:
        exists = db.execute(select(Tribe).where(Tribe.code==code)).scalar_one_or_none()
        if not exists:
            db.add(Tribe(code=code,name=name))

def seed_server(db):
    exists = db.execute(select(Server).where(Server.code=="api-test")).scalar_one_or_none()
    if not exists:
        db.add(Server(code="api-test",region="CN",speed="x1",start_date=date(2025,11,1),status="active"))

def seed_users_accounts_villages(db):
    u = db.execute(select(User).where(User.id==1)).scalar_one_or_none()
    if not u:
        db.add(User(id=1,nickname="tester"))
    s = db.execute(select(Server).where(Server.code=="api-test")).scalar_one()
    rom = db.execute(select(Tribe).where(Tribe.code=="ROM")).scalar_one()
    acc1 = db.execute(select(GameAccount).where(GameAccount.in_game_name=="player1")).scalar_one_or_none()
    if not acc1:
        acc1 = GameAccount(user_id=1,server_id=s.id,tribe_id=rom.id,in_game_name="player1")
        db.add(acc1)
    acc2 = db.execute(select(GameAccount).where(GameAccount.in_game_name=="player2")).scalar_one_or_none()
    if not acc2:
        acc2 = GameAccount(user_id=1,server_id=s.id,tribe_id=rom.id,in_game_name="player2")
        db.add(acc2)
    db.flush()
    v1 = db.execute(select(Village).where(Village.name=="Village1")).scalar_one_or_none()
    if not v1:
        db.add(Village(server_id=s.id,game_account_id=acc1.id,name="Village1",x=10,y=20))
    v2 = db.execute(select(Village).where(Village.name=="Village2")).scalar_one_or_none()
    if not v2:
        db.add(Village(server_id=s.id,game_account_id=acc2.id,name="Village2",x=11,y=21))

def seed_alliance(db):
    s = db.execute(select(Server).where(Server.code=="api-test")).scalar_one()
    a = db.execute(select(Alliance).where(Alliance.name=="AllianceOne")).scalar_one_or_none()
    if not a:
        a = Alliance(server_id=s.id,name="AllianceOne",tag="AL1",description="demo",created_by=1)
        db.add(a)
        db.flush()
    acc1 = db.execute(select(GameAccount).where(GameAccount.in_game_name=="player1")).scalar_one()
    m1 = db.execute(select(AllianceMember).where(AllianceMember.alliance_id==a.id,AllianceMember.game_account_id==acc1.id)).scalar_one_or_none()
    if not m1:
        db.add(AllianceMember(alliance_id=a.id,game_account_id=acc1.id,server_id=s.id,role="leader",join_status="active"))

def seed_troop_types_from_json(db):
    base = os.path.abspath(os.path.join(os.path.dirname(__file__),"..","data","troops_t4.6_1x.json"))
    if not os.path.exists(base):
        return
    with open(base,"r",encoding="utf-8") as f:
        data = json.load(f)
    for tribe in data.get("tribes", []):
        tid = int(tribe.get("tribeId"))
        for idx,u in enumerate(tribe.get("units", []), start=1):
            code = f"T{tid}-{idx}"
            name = u.get("name") or code
            exists = db.execute(select(TroopType).where(TroopType.tribe_id==tid,TroopType.code==code)).scalar_one_or_none()
            if not exists:
                db.add(TroopType(tribe_id=tid,code=code,name=name))

def main():
    ensure_tables()
    with SessionLocal() as db:
        seed_tribes(db)
        seed_server(db)
        seed_users_accounts_villages(db)
        seed_alliance(db)
        seed_troop_types_from_json(db)
        db.commit()
    print("OK")

if __name__ == "__main__":
    main()