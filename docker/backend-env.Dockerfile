# This is Backend Environment File 
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    tini \
    build-essential \
    libpq-dev \
    texlive \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-lang-english \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir uv 

COPY requirements.txt /app/requirements.txt
RUN uv pip install --system -r /app/requirements.txt

