# Manual `docker build .` defaults to amd64. CI passes arm64 explicitly for
# the native ARM runner.
ARG TARGETARCH=amd64
FROM registry.cn-shanghai.aliyuncs.com/jing-images/linux_${TARGETARCH}_alpine:3.20.3

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
