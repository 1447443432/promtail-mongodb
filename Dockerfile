# Manual builds use the official multi-architecture Alpine image. CI passes
# BASE_IMAGE explicitly, so projects with different amd64/arm64 base images
# can still override it per architecture.
ARG BASE_IMAGE=alpine:3.23
FROM ${BASE_IMAGE}

ARG TARGETARCH

RUN echo "https://mirrors.aliyun.com/alpine/v3.23/main" > /etc/apk/repositories \
    && echo "https://mirrors.aliyun.com/alpine/v3.23/community" >> /etc/apk/repositories \
    && apk update \
    && apk add --no-cache \
       loki-promtail \
       ca-certificates \
       tzdata \
    && mkdir -p /data/promtail /etc/promtail \
    && rm -rf /var/cache/apk/*

COPY config/promtail-config.yaml /etc/promtail/promtail-config.yaml

COPY config/positions.yaml /data/promtail/positions.yaml

COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /etc/promtail

EXPOSE 9081

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
