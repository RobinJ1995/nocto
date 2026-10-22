FROM node:24

RUN apt-get update \
    && apt-get install -y --no-install-recommends webp \
    && rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN \
  sh fullinstall-ci.sh && \
  chown node:node logs persist
  #sh fullinstall-prod.sh

USER node

VOLUME ["/usr/src/app/logs", "/usr/src/app/persist"]

CMD node nocto.js
