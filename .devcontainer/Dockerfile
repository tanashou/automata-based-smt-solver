FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

WORKDIR /app

# Copy only necessary files for installation
COPY pyproject.toml .

# Install Java, ANTLR4, and other dependencies in a single RUN command
ENV ANTLR_VERSION=4.13.2 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH=$PATH:/usr/lib/jvm/java-17-openjdk-amd64/bin \
    CLASSPATH=.:/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    graphviz \
    graphviz-dev \
    sudo \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install ANTLR4 tools
RUN wget --progress=dot:giga https://www.antlr.org/download/antlr-$ANTLR_VERSION-complete.jar -O /usr/local/lib/antlr-$ANTLR_VERSION-complete.jar && \
    printf '#!/bin/bash\njava -jar /usr/local/lib/antlr-%s-complete.jar "$@"' "$ANTLR_VERSION" > /usr/local/bin/antlr4 && \
    chmod +x /usr/local/bin/antlr4 && \
    printf '#!/bin/bash\njava org.antlr.v4.gui.TestRig "$@"' > /usr/local/bin/grun && \
    chmod +x /usr/local/bin/grun

COPY . .

# Install build dependencies and the package. Also, install this project in editable mode.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --editable ".[dev]"
