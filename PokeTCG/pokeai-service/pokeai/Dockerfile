FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8765

CMD ["python", "-B", "api_server.py", "--host", "0.0.0.0", "--port", "8765"]
