ARG UV_VERSION=0.9.7
ARG MINICONDA_TAG=25.3.1-1

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM continuumio/miniconda3:${MINICONDA_TAG}

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

ARG USERNAME=absmt-user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN chown -R $USERNAME:$USERNAME /opt/conda/envs/${CONDA_ENV_NAME} /app

USER $USERNAME

ENV PATH="/opt/conda/envs/${CONDA_ENV_NAME}/bin:$PATH"

RUN conda init bash && \
    echo "conda activate ${CONDA_ENV_NAME}" >> ~/.bashrc

COPY --chown=$USERNAME:$USERNAME . .

RUN uv pip sync pyproject.toml && \
    uv pip install setuptools && \
    uv pip install --group test -r pyproject.toml && \
    uv pip install .

CMD ["bash"]
