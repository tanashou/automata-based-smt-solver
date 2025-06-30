ARG UV_VERSION=latest
ARG MINICONDA_VERSION=3

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM mcr.microsoft.com/devcontainers/miniconda:${MINICONDA_VERSION}

ARG USER_NAME=vscode

# TODO: manage conda env name in one place.
ARG CONDA_ENV_NAME=absmt

COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && rm /tmp/environment.yml
# setup for activating created conda env when starting a shell
RUN echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/${USER_NAME}/.bashrc && \
    echo "conda activate ${CONDA_ENV_NAME}" >> /home/${USER_NAME}/.bashrc

COPY --from=uv --chown=${USER_NAME}: /uv /uvx /bin/
ENV UV_LINK_MODE=copy

RUN chown -R ${USER_NAME}:${USER_NAME} /opt/conda/envs/${CONDA_ENV_NAME}
ENV UV_PYTHON=/opt/conda/envs/${CONDA_ENV_NAME}/bin/python
