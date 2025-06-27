ARG UV_VERSION=latest
ARG DEBIAN_VERSION=bookworm

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM mcr.microsoft.com/vscode/devcontainers/base:${DEBIAN_VERSION}

# Add proxy configuration to fix "Hash sum mismatch" error
RUN echo 'Acquire::http::Pipeline-Depth 0;' >> /etc/apt/apt.conf.d/99fixbadproxy \
    && echo 'Acquire::http::No-Cache true;' >> /etc/apt/apt.conf.d/99fixbadproxy \
    && echo 'Acquire::BrokenProxy true;' >> /etc/apt/apt.conf.d/99fixbadproxy

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz graphviz-dev gcc \
    # To remove the image size, it is recommended refresh the package cache as follows
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv --chown=vscode: /uv /uvx /bin/
