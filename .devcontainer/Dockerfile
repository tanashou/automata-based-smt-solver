ARG UV_VERSION=latest
ARG MINICONDA_VERSION=3

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM mcr.microsoft.com/devcontainers/miniconda:${MINICONDA_VERSION}

ARG USER_NAME=vscode

# Latest version for linux-aarch64
ARG SPOT_VERSION=2.12
# for this spot version, conda version does not have the latest spot and cannot use python 3.13.
ARG PYTHON_VERSION=3.12
ARG CONDA_ENV_NAME=absmt

# install spot
RUN conda create -y --name ${CONDA_ENV_NAME} python=${PYTHON_VERSION} && \
    conda install -y -n ${CONDA_ENV_NAME} -c conda-forge spot=${SPOT_VERSION} && \
    conda clean -afy

# setup for activating created conda env when starting a shell
RUN echo ". /opt/conda/etc/profile.d/conda.sh" >> /home/${USER_NAME}/.bashrc && \
    echo "conda activate ${CONDA_ENV_NAME}" >> /home/${USER_NAME}/.bashrc

COPY --from=uv --chown=${USER_NAME}: /uv /uvx /bin/
ENV UV_LINK_MODE=copy

RUN chown -R ${USER_NAME}:${USER_NAME} /opt/conda/envs/${CONDA_ENV_NAME}
ENV UV_PYTHON=/opt/conda/envs/${CONDA_ENV_NAME}/bin/python
