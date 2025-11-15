FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend_py/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend_py /app

EXPOSE 8080

CMD ["gunicorn", "--chdir", "/app", "-w", "2", "-b", "0.0.0.0:8080", "app:app"]