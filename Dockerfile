FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG SUPERCRONIC_VERSION=v0.2.39

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl tzdata \
    && arch="$(dpkg --print-architecture)" \
    && case "$arch" in \
        amd64) supercronic_arch="amd64" ;; \
        arm64) supercronic_arch="arm64" ;; \
        *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; \
      esac \
    && curl -fsSLo /usr/local/bin/supercronic "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${supercronic_arch}" \
    && chmod +x /usr/local/bin/supercronic \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN chmod +x docker/scheduler-entrypoint.sh docker/run-main.sh

CMD ["python", "main.py"]
