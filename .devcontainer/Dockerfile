FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

WORKDIR /app

COPY pyproject.toml .
COPY src ./src


RUN apt-get update && \
    apt-get install -y graphviz graphviz-dev sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Install build dependencies and the package
    pip install --upgrade pip && \
    pip install ".[dev]"

COPY . .
