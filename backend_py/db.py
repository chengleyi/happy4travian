import os
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

m_jdbc = os.getenv("SPRING_DATASOURCE_URL", "")
user_raw = os.getenv("SPRING_DATASOURCE_USERNAME", "")
password_raw = os.getenv("SPRING_DATASOURCE_PASSWORD", "")
m = re.match(r"jdbc:mysql://([^/:]+)(?::(\d+))?/([^?]+)", m_jdbc)
host = m.group(1) if m else "localhost"
port = int(m.group(2)) if m and m.group(2) else 3306
dbname = m.group(3) if m else "happy4travian"
user = quote_plus(user_raw or "")
password = quote_plus(password_raw or "")
url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()