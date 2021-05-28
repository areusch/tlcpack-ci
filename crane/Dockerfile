FROM docker:20.10.5

RUN apk add --no-cache \
    ansible \
    bash \
    git \
    python3 \
    sudo \
    terraform

RUN python3 -mensurepip

RUN pip3 install poetry
