ARG UV_VERSION=latest
ARG MINICONDA_VERSION=latest

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM continuumio/miniconda3:${MINICONDA_VERSION}

WORKDIR /app

ARG CONDA_ENV_NAME=absmt

COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && \
    rm /tmp/environment.yml && \
    conda clean -afy

# Install uv
COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy

ENV UV_PYTHON=/opt/conda/envs/${CONDA_ENV_NAME}/bin/python

# Need this for 'uv pip sync' to work
COPY pyproject.toml README.md LICENSE ./

RUN uv pip sync pyproject.toml && \
    uv pip install .
