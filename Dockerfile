# Manual `docker build .` defaults to the amd64 base image. CI passes the
# architecture-specific BASE_IMAGE explicitly, so amd64 and arm64 may use
# completely different repositories, names, or tags.
ARG BASE_IMAGE=registry.cn-shanghai.aliyuncs.com/jing-images/linux_amd64_alpine:3.20.3
FROM ${BASE_IMAGE}

ARG TARGETARCH

RUN echo "https://mirrors.aliyun.com/alpine/v3.20/main" > /etc/apk/repositories \
    && echo "https://mirrors.aliyun.com/alpine/v3.20/community" >> /etc/apk/repositories \
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
