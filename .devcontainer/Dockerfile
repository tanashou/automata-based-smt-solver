FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

WORKDIR /app

# Copy only necessary files for installation
COPY pyproject.toml .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    graphviz \
    graphviz-dev \
    sudo \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir --upgrade pip==23.1 && \
    pip install --no-cache-dir --editable ".[dev]"
