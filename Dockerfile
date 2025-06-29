ARG UV_VERSION=latest
ARG MINICONDA_VERSION=3

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM continuumio/miniconda3:${MINICONDA_VERSION}

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml ./

# Latest version for linux-aarch64
ARG SPOT_VERSION=2.12
# for this spot version, conda version does not have the latest spot and cannot use python 3.13.
ARG PYTHON_VERSION=3.12
ARG CONDA_ENV_NAME=absmt

# install spot
RUN conda create -y --name ${CONDA_ENV_NAME} python=${PYTHON_VERSION} && \
    conda install -y -n ${CONDA_ENV_NAME} -c conda-forge spot=${SPOT_VERSION} && \
    conda clean -afy

COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy

ENV UV_PYTHON=/opt/conda/envs/${CONDA_ENV_NAME}/bin/python

RUN uv pip sync pyproject.toml && \
    uv pip install -e .
