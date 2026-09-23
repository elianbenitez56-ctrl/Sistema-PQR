# Cómo ejecutar el proyecto

## 1. Con Docker (recomendado)

Requisitos: Docker y Docker Compose v2.

```bash
cp .env.example .env
```

Complete al menos estas variables en `.env`:

| Variable | Para qué |
|---|---|
| `SECRET_KEY` | Firma de las sesiones. Genere una con `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASS` | Contraseña del usuario `admin`, que se crea en el primer arranque |
| `PGPASSWORD` | Contraseña de PostgreSQL (la usan tanto el contenedor `db` como la app) |

Luego:

```bash
docker compose up --build
```

- Aplicación: <http://localhost:8000> (el puerto se cambia con `PORT` en `.env`).
- PostgreSQL desde su máquina (opcional): `127.0.0.1:5434`, usuario y contraseña de `.env`.
- El primer arranque crea las tablas y siembra `admin` y los usuarios de `app/semillas.py`.

`docker compose up` aplica automáticamente `docker-compose.override.yml` (modo desarrollo): servidor Flask con
recarga al guardar, código montado desde su carpeta y herramientas de desarrollo (`pytest`, `ruff`) instaladas.

Para probar la imagen tal como se despliega (gunicorn, sin recarga):

```bash
docker compose -f docker-compose.yml up --build
```

> En este modo las cookies de sesión son `Secure`: algunos navegadores (p. ej. Safari) las rechazan por
> `http://localhost` y el login no se mantiene. En ese caso agregue `SESSION_COOKIE_SECURE=0` en `.env`.

### Datos persistentes

| Volumen | Contenido |
|---|---|
| `postgres_data` | Base de datos |
| `evidencias` | Archivos adjuntos subidos (`/data/evidencias` en el contenedor) |

`docker compose down` conserva los datos; `docker compose down -v` los **borra**.

## 2. Sin Docker

Requisitos: Python 3.12 y un servidor PostgreSQL 14+ con una base creada
(`createdb sistema_pqr` o `CREATE DATABASE sistema_pqr;`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export FLASK_DEBUG=1 SECRET_KEY=dev ADMIN_PASS=admin123
export PGHOST=127.0.0.1 PGUSER=pqr PGPASSWORD=... PGDATABASE=sistema_pqr PGSSLMODE=disable
flask --app wsgi run --debug --port 8000
```

> La aplicación **no lee `.env`** salvo para las variables de correo (`SMTP_*`). Las demás deben estar
> exportadas en el entorno (o cargadas con `set -a; source .env; set +a`).

## 3. Variables de entorno

| Variable | Obligatoria | Por defecto | Descripción |
|---|---|---|---|
| `SECRET_KEY` | Sí (salvo `FLASK_DEBUG=1`) | — | Clave de firma de sesiones |
| `ADMIN_PASS` | Sí, en el primer arranque | — | Contraseña inicial de `admin` |
| `PGHOST` | Sí | `localhost` | Servidor PostgreSQL (`db` dentro de Docker Compose) |
| `PGPORT` | No | `5432` | Puerto PostgreSQL |
| `PGUSER` | Sí | `postgres` | Usuario PostgreSQL |
| `PGPASSWORD` | Sí | vacío | Contraseña PostgreSQL |
| `PGDATABASE` | No | `sistema_pqr` | Nombre de la base |
| `PGSSLMODE` | No | `prefer` | `require` en Supabase/Neon; `disable` en Docker Compose local |
| `PG_POOL_SIZE` | No | `16` | Conexiones por proceso |
| `SEED_USER_PASSWORD` | No | la de `app/semillas.py` | Contraseña inicial de los usuarios sembrados |
| `PQR_UPLOAD_DIR` | No | `Base_Datos/Evidencias` (`/data/evidencias` en Docker) | Carpeta de evidencias |
| `MAX_UPLOAD_MB` | No | `25` | Tamaño máximo por petición de subida |
| `CATALOGO_PRODUCTOS_PATH` | No | `datos/LISTADO PRODUCTOS.xlsx` | Catálogo maestro de productos |
| `PQR_URL_BASE` | Recomendada | — | URL pública, usada en los enlaces de los correos |
| `SMTP_HOST`, `SMTP_PORT` | Para correo | — / `587` | Servidor SMTP (Gmail: `smtp.gmail.com`, `587`) |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Para correo | — | Credenciales y remitente. En Gmail use una *contraseña de aplicación* |
| `SMTP_USE_TLS`, `SMTP_USE_SSL` | No | `true` / `false` | Cifrado del SMTP |
| `FLASK_DEBUG` | No | — | `1` = modo desarrollo (permite `SECRET_KEY` por defecto y cookies sin `Secure`) |
| `SESSION_COOKIE_SECURE` | No | `1` (`0` con `FLASK_DEBUG=1`) | Cookies solo por HTTPS |
| `TRUST_PROXY` | No | `0` (`1` en la imagen) | Confiar en `X-Forwarded-*` de un proxy (Render) |

Si faltan las variables `SMTP_*`, la aplicación funciona igual pero **no envía correos**.

Probar el envío de correo: `docker compose exec web python -m scripts.test_smtp`.

## 4. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `RuntimeError: SECRET_KEY es obligatoria` | Defina `SECRET_KEY` en `.env` (o use `FLASK_DEBUG=1` en desarrollo) |
| `ADMIN_PASS debe configurarse antes de crear el administrador` | Defina `ADMIN_PASS` antes del primer arranque |
| `docker compose` pide `PGPASSWORD` | Falta en `.env` |
| El login no se mantiene en modo producción local | Cookies `Secure` sobre HTTP: use `SESSION_COOKIE_SECURE=0` o HTTPS |
| `web` reintenta conectarse a PostgreSQL varios segundos | Normal: espera hasta 60 s a que la base esté lista |
| `password authentication failed` tras cambiar la contraseña | El volumen conserva la contraseña original: `docker compose down -v` (borra datos) o cambie la clave dentro de Postgres |
| `SSL connection is required` contra Supabase/Neon | Defina `PGSSLMODE=require` |
| No llegan correos | Revise `SMTP_*`, use contraseña de aplicación de Gmail y ejecute `scripts.test_smtp` |
| Puerto 8000 ocupado | Defina `PORT=8080` en `.env` |
