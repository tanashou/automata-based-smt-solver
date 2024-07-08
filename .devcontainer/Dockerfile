FROM python:3.11

ARG PROJECT_NAME
WORKDIR /workspaces/${PROJECT_NAME}

# sudoできる権限を持ったvscodeユーザを作成
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN apt-get update && \
    apt-get install -y graphviz graphviz-dev sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    groupadd --gid $USER_GID $USERNAME && \
    useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# Install Hatchling and pip-tools
RUN pip install --no-cache-dir hatchling

COPY . .

RUN pip install .