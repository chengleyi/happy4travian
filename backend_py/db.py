"""数据库连接与会话工厂

从环境变量读取 MySQL 连接信息（兼容 Spring 格式 jdbc URL），
构建 SQLAlchemy `engine`、`SessionLocal` 以及 `Base`。
"""
import os
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

 # 读取环境变量（由部署注入），兼容 jdbc:mysql://host:port/dbname
m_jdbc = os.getenv("SPRING_DATASOURCE_URL", "")
user_raw = os.getenv("SPRING_DATASOURCE_USERNAME", "")
password_raw = os.getenv("SPRING_DATASOURCE_PASSWORD", "")
 # 解析 JDBC URL，提取主机、端口与库名
m = re.match(r"jdbc:mysql://([^/:]+)(?::(\d+))?/([^?]+)", m_jdbc)
host = m.group(1) if m else "localhost"
port = int(m.group(2)) if m and m.group(2) else 3306
dbname = m.group(3) if m else "happy4travian"
user = quote_plus(user_raw or "")
password = quote_plus(password_raw or "")
url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}?charset=utf8mb4"
# 创建引擎与会话（开启 pre_ping 以避免连接失效，并强制连接层使用 utf8mb4）
engine = create_engine(url, pool_pre_ping=True, connect_args={"charset":"utf8mb4"})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
# 声明基类，用于模型定义
Base = declarative_base()