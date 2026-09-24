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

# WeasyPrint is not pure Python. weasyprint.text.ffi dlopens pango, pangoft2, harfbuzz,
# fontconfig and gobject through cffi, and harfbuzz-subset performs the font subsetting
# (WeasyPrint 70 warns that it will be required). A `pip install weasyprint` therefore
# imports fine and then dies on the first render in a slim image, which ships neither the
# libraries nor a single text family. libpangoft2-1.0-0 pulls pango, fontconfig,
# harfbuzz and glib (gobject) with it; libc/glibc and libstdc++/libgcc (node's runtime)
# are already in the base, since apt itself links them.
# gdk-pixbuf and cairo are deliberately NOT installed: WeasyPrint 70 renders SVG with its
# own engine and raster images through Pillow (checked against the installed package —
# neither name appears in a single import).
RUN apt-get update \
 && apt-get install --no-install-recommends --yes \
      libpangoft2-1.0-0 \
      libharfbuzz-subset0 \
      shared-mime-info \
      fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

# Node is copied in (not installed) because KaTeX renders server-side for the
# PDF: same source of truth as the screen, no markup accepted from clients.
# Binaries built against glibc 2.36 (bookworm) run on trixie's 2.41.
COPY --from=web /usr/local/bin/node /usr/local/bin/node

# The katex package the frontend bundle already vendors. app/render/pdf.py runs
# `katex.renderToString` through that node binary once per document, so screen and PDF
# share one KaTeX version and one LaTeX source; /opt/katex is that module's default
# location (TEACHING_KATEX_DIR overrides it).
COPY --from=web /web/node_modules/katex/dist /opt/katex

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
