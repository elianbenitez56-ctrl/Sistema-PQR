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
| `MYSQL_PASSWORD` | Contraseña del usuario de aplicación de MySQL |
| `MYSQL_ROOT_PASSWORD` | Contraseña root de MySQL (solo el contenedor `db`) |

Luego:

```bash
docker compose up --build
```

- Aplicación: <http://localhost:8000> (el puerto se cambia con `PORT` en `.env`).
- MySQL desde su máquina (opcional): `127.0.0.1:3307`, usuario y contraseña de `.env`.
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
| `mysql_data` | Base de datos |
| `evidencias` | Archivos adjuntos subidos (`/data/evidencias` en el contenedor) |

`docker compose down` conserva los datos; `docker compose down -v` los **borra**.

## 2. Sin Docker

Requisitos: Python 3.12 y un servidor MySQL 8 con una base y un usuario creados
(`CREATE DATABASE sistema_pqr CHARACTER SET utf8mb4;`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

export FLASK_DEBUG=1 SECRET_KEY=dev ADMIN_PASS=admin123
export MYSQL_HOST=127.0.0.1 MYSQL_USER=pqr MYSQL_PASSWORD=... MYSQL_DATABASE=sistema_pqr
flask --app wsgi run --debug --port 8000
```

> La aplicación **no lee `.env`** salvo para las variables de correo (`SMTP_*`). Las demás deben estar
> exportadas en el entorno (o cargadas con `set -a; source .env; set +a`).

## 3. Variables de entorno

| Variable | Obligatoria | Por defecto | Descripción |
|---|---|---|---|
| `SECRET_KEY` | Sí (salvo `FLASK_DEBUG=1`) | — | Clave de firma de sesiones |
| `ADMIN_PASS` | Sí, en el primer arranque | — | Contraseña inicial de `admin` |
| `MYSQL_HOST` | Sí | `localhost` | Servidor MySQL (`db` dentro de Docker Compose) |
| `MYSQL_PORT` | No | `3306` | Puerto MySQL |
| `MYSQL_USER` | Sí | `root` | Usuario MySQL |
| `MYSQL_PASSWORD` | Sí | vacío | Contraseña MySQL |
| `MYSQL_DATABASE` | No | `sistema_pqr` | Nombre de la base |
| `MYSQL_POOL_SIZE` | No | `16` | Conexiones por proceso |
| `MYSQL_ROOT_PASSWORD` | Solo compose | — | Contraseña root del contenedor MySQL |
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
| `docker compose` pide `MYSQL_ROOT_PASSWORD`/`MYSQL_PASSWORD` | Faltan en `.env` |
| El login no se mantiene en modo producción local | Cookies `Secure` sobre HTTP: use `SESSION_COOKIE_SECURE=0` o HTTPS |
| `web` reintenta conectarse a MySQL varios segundos | Normal: espera hasta 60 s a que MySQL esté listo |
| `Access denied for user` tras cambiar la contraseña de MySQL | El volumen conserva la contraseña original: `docker compose down -v` (borra datos) o cambie la clave dentro de MySQL |
| No llegan correos | Revise `SMTP_*`, use contraseña de aplicación de Gmail y ejecute `scripts.test_smtp` |
| Puerto 8000 ocupado | Defina `PORT=8080` en `.env` |
