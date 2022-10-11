FROM mcr.microsoft.com/vscode/devcontainers/python:3.10
ENV EDITOR=vim

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y vim gnupg2 ripgrep
