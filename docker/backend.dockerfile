FROM ubuntu:latest

LABEL Maintainer=adityanile<adityanile@gmail.com>

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ca-certificates \
    texlive-latex-recommended \
    texlive \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-lang-all \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages uv

COPY docker/requirements.txt /app/requirements.txt
RUN uv pip install --system --break-system-packages --prerelease=allow --no-cache -r /app/requirements.txt

#COPY . /app
