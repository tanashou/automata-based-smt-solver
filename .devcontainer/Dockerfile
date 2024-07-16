FROM python:3.11

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



# root 権限を持ったvscodeユーザーの作成
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

# Set correct ownership and permissions
RUN chown -R vscode:vscode /app
RUN chmod -R 755 /app

# Switch to vscode user
USER vscode

