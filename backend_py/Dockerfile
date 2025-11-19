# 使用轻量化 Python 3.11 基础镜像
FROM python:3.11-slim

# 关闭 .pyc 写入，开启无缓冲输出，便于日志观察
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 设置应用工作目录
WORKDIR /app

# 安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*
COPY backend_py/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 拷贝后端代码到镜像
COPY backend_py /app
COPY resource /app/resource

# 暴露对外端口（gunicorn 监听 8080）
EXPOSE 8080

# 使用 gunicorn 启动 Flask 应用
CMD ["gunicorn", "--chdir", "/app", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]