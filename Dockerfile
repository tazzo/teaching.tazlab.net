# syntax=docker/dockerfile:1
# --- Stage 1: frontend bundle (Vite 8) -------------------------------------
FROM node:24-bookworm AS web

WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- Stage 2: runtime (FastAPI + SymPy + WeasyPrint) ----------------------
FROM python:3.14-slim

# Node is copied in (not installed) because KaTeX renders server-side for the
# PDF: same source of truth as the screen, no markup accepted from clients.
# Binaries built against glibc 2.36 (bookworm) run on trixie's 2.41.
COPY --from=web /usr/local/bin/node /usr/local/bin/node

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TEACHING_LOG_LEVEL=INFO

WORKDIR /app

# Dependencies first (slow, rarely changing) — read from pyproject so it stays the
# single source of truth; then the application, which setuptools needs present.
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
 && python -c "import pathlib,tomllib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print(chr(10).join(d['project']['dependencies']))" > /tmp/requirements.txt \
 && pip install --no-cache-dir -r /tmp/requirements.txt

COPY app/ ./app/
RUN pip install --no-cache-dir --no-deps .
COPY --from=web /web/dist ./web/dist

# git sha of the image build, surfaced in the startup banner
ARG GIT_SHA=unknown
ENV TEACHING_GIT_SHA=${GIT_SHA}

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin teaching
USER 10001

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "2", "--forwarded-allow-ips", "10.244.0.0/16", \
     "--timeout-graceful-shutdown", "25", "--no-access-log"]
