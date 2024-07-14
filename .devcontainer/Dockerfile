FROM python:3.11
RUN pip install --upgrade pip && \
    pip install hatch

WORKDIR /app
COPY pyproject.toml /app

RUN apt-get update && \
    apt-get install -y graphviz graphviz-dev sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    hatch dep show requirements > /app/requirements.txt && \
    python -m pip install -r /app/requirements.txt

COPY . /app
RUN python -m pip install -e .

# root 権限を持ったvscodeユーザーの作成
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME
