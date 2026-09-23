# Sistema PQR — INAPEL

Aplicación web para registrar, investigar y dar seguimiento a **Peticiones, Quejas y Reclamos (PQR)** de clientes.
Flask (Python 3.12) + PostgreSQL, empaquetada con Docker y desplegada en Render (base en Supabase/Neon).

## Qué hace

- Los **vendedores** registran PQR de sus clientes (con productos del catálogo maestro y evidencias adjuntas). El cliente recibe un correo de confirmación con su radicado.
- **Calidad** investiga cada PQR (causa, herramientas de análisis, departamentos) y **Comercial** responde al cliente y cierra el caso.
- Cada PQR recorre un flujo de estados con historial completo. Un dashboard resume conteos por estado, tipo y prioridad.
- Acceso por roles (administrador, líder de calidad, líder/coordinación/dirección comercial, comercial, vendedor).

## Inicio rápido

Requisitos: [Docker](https://docs.docker.com/get-docker/) con Docker Compose.

```bash
cp .env.example .env
# Edite .env: SECRET_KEY, ADMIN_PASS y PGPASSWORD (obligatorios)
docker compose up --build
```

Abra <http://localhost:8000> e ingrese con usuario `admin` y la contraseña definida en `ADMIN_PASS`.

Para generar un `SECRET_KEY`: `python3 -c "import secrets; print(secrets.token_hex(32))"`.

## Comandos habituales

| Acción | Comando |
|---|---|
| Levantar en desarrollo (recarga automática) | `docker compose up --build` |
| Levantar como producción (gunicorn) | `docker compose -f docker-compose.yml up --build` |
| Tests | `docker compose exec web pytest -q` |
| Lint | `docker compose exec web ruff check .` |
| Ver logs | `docker compose logs -f web` |
| Detener | `docker compose down` |
| Detener y **borrar datos** (base y evidencias) | `docker compose down -v` |

## Documentación

| Documento | Contenido |
|---|---|
| [docs/ejecucion.md](docs/ejecucion.md) | Cómo ejecutar el proyecto (Docker y sin Docker), variables de entorno, problemas frecuentes |
| [docs/arquitectura.md](docs/arquitectura.md) | Estructura del código, flujo de una petición, base de datos, seguridad, reglas de negocio |
| [docs/api.md](docs/api.md) | Endpoints, permisos por rol y estados del PQR |
| [docs/desarrollo.md](docs/desarrollo.md) | Flujo de trabajo, tests, lint, CI y cómo agregar funcionalidades |
| [docs/despliegue.md](docs/despliegue.md) | Despliegue en Render y operación en producción |
| [docs/diseno/](docs/diseno/) | Mockups y guías visuales de las pantallas |

## Estructura del repositorio

```
wsgi.py            punto de entrada (gunicorn wsgi:app)
app/               código de la aplicación (ver docs/arquitectura.md)
datos/             catálogo maestro de productos (LISTADO PRODUCTOS.xlsx)
docs/              documentación
scripts/           utilidades (p. ej. prueba de SMTP)
tests/             pruebas automatizadas
Dockerfile, docker-compose*.yml, render.yaml   contenedores y despliegue
```
