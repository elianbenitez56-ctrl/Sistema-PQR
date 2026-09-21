# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Flask single-page app (`templates/index.html`, inline CSS/JS) for PQR management (Peticiones/Quejas/Reclamos) at INAPEL. MySQL storage (`mysql_db.py`), Docker for dev and deploy (Render, `runtime: docker`). `AGENTS.md` still has a useful endpoint/roles table, but its Excel/storage sections are obsolete.

## Commands

```bash
cp .env.example .env            # fill SECRET_KEY, ADMIN_PASS, MYSQL_* (compose needs MYSQL_ROOT_PASSWORD and MYSQL_PASSWORD)
docker compose up --build       # dev: override file enables flask --debug + code bind-mount, http://localhost:8000
docker compose -f docker-compose.yml up --build   # prod-like: gunicorn, no override
docker compose exec web python -m pytest -q tests # smoke tests (need the MySQL container)
docker compose exec web python -m scripts.test_smtp  # SMTP sanity check
```

## Architecture

- `app.py`: config from env, `asegurar_tablas()` (waits for MySQL, creates schema) + `sembrar_usuarios()` at import time, `/healthz` (does `SELECT 1`). `SECRET_KEY` is mandatory unless `FLASK_DEBUG=1`.
- `mysql_db.py`: all data access (pooled connections, `get_db_cursor`), schema in `SCHEMA_SQL`, user CRUD/auth, PQR CRUD, dashboard, seeding. Note MySQL 8 rejects `TEXT DEFAULT ''`; use `DEFAULT ('')`. `generar_radicado()` is read-last-then-write (race under concurrency).
- `routes.py`: single blueprint, session-cookie auth with roles (`rol_requerido`), login rate limit (in-memory per worker), evidence upload validated by `RADICADO_RE` + extension whitelist.
- `email_service.py`: Gmail SMTP via `SMTP_*` env vars. `catalogo_productos.py`: product list from `datos/LISTADO PRODUCTOS.xlsx` (non-fatal on failure).
- `usuarios_iniciales.py`: seed users (temporary shared password inside; replace before real use).
- Evidence files go to `PQR_UPLOAD_DIR` (`/data/evidencias`, a Docker volume). On Render they persist only if a paid disk is mounted (see `render.yaml`).
- Deploy: Render builds the `Dockerfile`; MySQL must be an external managed instance (`MYSQL_HOST/USER/PASSWORD` env vars).
