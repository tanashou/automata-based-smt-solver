# FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# WORKDIR /app

# COPY pyproject.toml .
# COPY src ./src

# # Install Java (required for ANTLR4)
# RUN apt-get update && \
#     apt-get -y install openjdk-17-jdk && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Set JAVA_HOME environment variable
# ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64
# ENV PATH $PATH:$JAVA_HOME/bin

# # Install ANTLR4 tools
# ENV ANTLR_VERSION 4.13.2
# RUN wget https://www.antlr.org/download/antlr-$ANTLR_VERSION-complete.jar -O /usr/local/lib/antlr-$ANTLR_VERSION-complete.jar && \
#     echo '#!/bin/bash\njava -jar /usr/local/lib/antlr-$ANTLR_VERSION-complete.jar "$@"' > /usr/local/bin/antlr4 && \
#     chmod +x /usr/local/bin/antlr4 && \
#     echo '#!/bin/bash\njava org.antlr.v4.gui.TestRig "$@"' > /usr/local/bin/grun && \
#     chmod +x /usr/local/bin/grun

# # Set CLASSPATH for ANTLR4
# ENV CLASSPATH .:/usr/local/lib/antlr-$ANTLR_VERSION-complete.jar:$CLASSPATH

# RUN apt-get update && \
#     apt-get install -y graphviz graphviz-dev sudo && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/* && \
#     # Install build dependencies and the package
#     pip install --upgrade pip && \
#     pip install ".[dev]"

# COPY . .

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
    rm -rf /var/lib/apt/lists/* && \
    # Install ANTLR4 tools
    wget https://www.antlr.org/download/antlr-$ANTLR_VERSION-complete.jar -O /usr/local/lib/antlr-$ANTLR_VERSION-complete.jar && \
    echo '#!/bin/bash\njava -jar /usr/local/lib/antlr-$ANTLR_VERSION-complete.jar "$@"' > /usr/local/bin/antlr4 && \
    chmod +x /usr/local/bin/antlr4 && \
    echo '#!/bin/bash\njava org.antlr.v4.gui.TestRig "$@"' > /usr/local/bin/grun && \
    chmod +x /usr/local/bin/grun && \
    # Install build dependencies and the package
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]"

COPY . .
