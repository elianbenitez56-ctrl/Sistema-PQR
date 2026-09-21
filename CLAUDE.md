# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Flask single-page app (`templates/index.html`, inline CSS/JS) for PQR management (Peticiones/Quejas/Reclamos) at INAPEL. MySQL storage, Docker for dev and deploy (Render, `runtime: docker`). Full docs live in `docs/` (see `README.md` for the index); keep them in sync when changing endpoints, env vars or schema.

## Commands

```bash
cp .env.example .env            # fill SECRET_KEY, ADMIN_PASS, MYSQL_* (compose needs MYSQL_ROOT_PASSWORD and MYSQL_PASSWORD)
docker compose up --build       # dev: override file enables flask --debug + code bind-mount, http://localhost:8000
docker compose -f docker-compose.yml up --build   # prod-like: gunicorn, no override
docker compose exec web python -m pytest -q tests # smoke tests (need the MySQL container)
docker compose exec web python -m scripts.test_smtp  # SMTP sanity check
```

## Architecture

```
wsgi.py                 entrypoint (gunicorn wsgi:app / flask --app wsgi)
app/
  __init__.py           create_app(): config, schema, seed, catalog, blueprints, ErrorNegocio handler, /healthz
  config.py db.py       env config; MySQL pool + SCHEMA_SQL + migrations (asegurar_tablas)
  errores.py            ErrorNegocio(mensaje, status): services raise it, create_app turns it into JSON
  seguridad.py          roles + rol_requerido / sesion_requerida
  dominio.py            pure business rules (seguimiento state machine, herramientas) - no DB/Flask
  repos/                SQL only (usuarios.py, pqr.py) - no business decisions, commit=True on writes
  servicios/            use cases (pqr, seguimiento, usuarios) + correo (SMTP) + catalogo (xlsx)
  rutas/                thin Blueprints: read request -> call servicio -> jsonify
  semillas.py           seed users; SEED_USER_PASSWORD overrides their shared temporary password
  templates/ static/    single-page UI (index.html, inline CSS/JS)
datos/  docs/  scripts/  tests/
```

Dependency rule: `rutas -> servicios -> repos -> db`; services never touch Flask/HTTP.

- MySQL 8 rejects `TEXT DEFAULT ''`; use `DEFAULT ('')`. `generar_radicado()` is read-last-then-write (race under concurrency).
- Login rate limit is in-memory per worker (`rutas/sesion.py`); evidence upload validated by `RADICADO_RE` + extension whitelist (`rutas/evidencias.py`).
- Evidence files go to `PQR_UPLOAD_DIR` (`/data/evidencias`, a Docker volume). On Render they persist only if a paid disk is mounted (see `render.yaml`).
- Deploy: Render builds the `Dockerfile`; MySQL must be an external managed instance (`MYSQL_HOST/USER/PASSWORD` env vars).
- The `.env` loader in `servicios/correo.py` only matters outside Docker; compose injects env via `env_file`.
