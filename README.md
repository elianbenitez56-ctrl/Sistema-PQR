# Sistema PQR — INAPEL

Aplicación Flask (Python 3.12) + MySQL 8 para gestionar Peticiones, Quejas y Reclamos.

## Desarrollo local

```bash
cp .env.example .env        # completar SECRET_KEY, ADMIN_PASS, MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD
docker compose up --build   # http://localhost:8000 (recarga automática, MySQL en 127.0.0.1:3307)
```

Usuario inicial: `admin` con la contraseña de `ADMIN_PASS`.

## Calidad

```bash
docker compose exec web ruff check .          # lint
docker compose exec web python -m pytest -q   # tests (usan la base MySQL del compose)
```

CI (`.github/workflows/ci.yml`) ejecuta lo mismo en cada push y pull request.

## Estructura

| Ruta | Responsabilidad |
|---|---|
| `wsgi.py` | Punto de entrada (`gunicorn wsgi:app`) |
| `app/__init__.py`, `app/config.py` | Fábrica de la app y configuración por entorno |
| `app/db.py` | Pool MySQL, esquema y espera de arranque |
| `app/repos/` | Acceso a datos (SQL) por dominio |
| `app/rutas/` | Endpoints HTTP, un Blueprint por área |
| `app/servicios/` | Correo SMTP y catálogo de productos |
| `app/seguridad.py`, `app/validaciones.py` | Roles/decoradores y validaciones compartidas |
| `datos/`, `docs/`, `scripts/`, `tests/` | Catálogo, documentación, utilidades y pruebas |

Referencia de endpoints y roles: `AGENTS.md`.

## Despliegue (Render)

`render.yaml` construye el `Dockerfile`. Requiere una base MySQL externa (`MYSQL_HOST`, `MYSQL_USER`,
`MYSQL_PASSWORD`) y, para conservar evidencias entre despliegues, un disco persistente en `/data/evidencias`.
