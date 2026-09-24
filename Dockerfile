FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
ARG INSTALL_DEV=0
RUN if [ "$INSTALL_DEV" = "1" ]; then pip install -r requirements-dev.txt; else pip install -r requirements.txt; fi

COPY . .

RUN useradd --create-home app && mkdir -p /data/evidencias && chown -R app /app /data
USER app

# ponytail: TZ fija en <-05>5 (Colombia no tiene horario de verano); si el sistema opera en
# otro país con DST, cambiar por una zona de la base tz (p. ej. America/Bogota + paquete tzdata).
ENV PORT=8000 PQR_UPLOAD_DIR=/data/evidencias TRUST_PROXY=1 TZ=<-05>5
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import os,urllib.request as u; u.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz', timeout=4)"

CMD ["sh", "-c", "exec gunicorn wsgi:app --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 60 --access-logfile -"]
