FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/nexus \
    PATH=/usr/sbin:/home/nexus/.local/bin:/usr/local/bin:/usr/bin:/bin

RUN apt-get update \
    && apt-get install -y --no-install-recommends adduser \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 1000 nexus \
    && adduser --uid 1000 --disabled-password --gecos "" --home /home/nexus --ingroup nexus nexus \
    && mkdir -p /app /home/nexus/.local /audit /wallet /config \
    && chown -R nexus:nexus /app /home/nexus /audit /wallet /config

WORKDIR /app

COPY --chown=1000:1000 . /app

RUN chmod +x /app/healthcheck.sh

USER 1000:1000

RUN python -m pip install --no-cache-dir --user .

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD ["/bin/sh", "/app/healthcheck.sh"]

ENTRYPOINT ["/bin/sh", "-c", "chmod 600 /wallet/key.pem || true && python -m nexus_agent"]
