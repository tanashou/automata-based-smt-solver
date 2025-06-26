ARG VARIANT=3.13
ARG UV_VERSION=latest
ARG DEBIAN_VERSION=bookworm

FROM python:${VARIANT}-slim-${DEBIAN_VERSION} AS builder

# Add proxy configuration to fix "Hash sum mismatch" error
RUN echo 'Acquire::http::Pipeline-Depth 0;' >> /etc/apt/apt.conf.d/99fixbadproxy \
    && echo 'Acquire::http::No-Cache true;' >> /etc/apt/apt.conf.d/99fixbadproxy \
    && echo 'Acquire::BrokenProxy true;' >> /etc/apt/apt.conf.d/99fixbadproxy

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    # To remove the image size, it is recommended refresh the package cache as follows
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG DD_TAG=v0.6.0
RUN git clone --branch $DD_TAG --depth 1 https://github.com/tulip-control/dd.git /dd

WORKDIR /dd

# hadolint ignore=DL3013,DL3042
RUN pip install cython build setuptools
# Set environment variables required for the dd build
ENV DD_FETCH=1
ENV DD_CUDD=1
ENV DD_CUDD_ZDD=1
RUN python -m build --no-isolation


FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv
FROM python:$VARIANT-slim-$DEBIAN_VERSION

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

ENV PYTHONDONTWRITEBYTECODE=True
ENV PYTHONUNBUFFERED=True
ENV UV_LINK_MODE=copy

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

# Copy the custom wheel built in the previous stage
COPY --from=builder /dd/dist/dd-*.whl /dd/dist/

RUN uv lock --upgrade-package dd --find-links /dd/dist/ \
    && uv install --frozen --no-install-project
