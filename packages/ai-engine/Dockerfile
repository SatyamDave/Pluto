# syntax=docker/dockerfile:1
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001
ENV GIT_SHA=dev
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
