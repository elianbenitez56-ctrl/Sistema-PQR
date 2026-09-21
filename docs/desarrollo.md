# Guía de desarrollo

## Flujo de trabajo

1. `docker compose up --build` (recarga automática al guardar; ver [ejecucion.md](ejecucion.md)).
2. Haga los cambios en una rama: `git switch -c mi-cambio`.
3. Antes de subir: `docker compose exec web ruff check .` y `docker compose exec web pytest -q`.
4. Abra un pull request hacia `main`. El CI (`.github/workflows/ci.yml`) levanta MySQL 8.4 y ejecuta lint y tests.

Mensajes de commit: una línea que diga **qué y por qué** (en español, como el resto del historial).

## Tests

```bash
docker compose exec web pytest -q                      # todos
docker compose exec web pytest -q tests/test_pqr.py    # un archivo
docker compose exec web pytest -q -k seguimiento       # por nombre
```

Los tests usan la **base MySQL real** del compose (no hay mocks de base de datos), así que el contenedor `db` debe estar arriba.

| Archivo | Cubre |
|---|---|
| `tests/test_smoke.py` | Salud, login inválido, bloqueo por intentos, evidencias con radicado malicioso |
| `tests/test_pqr.py` | Flujo crear → consultar → cambiar estado → eliminar; seguimiento de Calidad (crear y actualizar) |
| `tests/test_permisos.py` | 401/403 por rol; el vendedor no ve PQR ajenos; editar, desactivar y eliminar usuarios persiste |
| `tests/test_flujos.py` | Catálogo, PQR con productos (y rechazo de inventados), evidencias (subida, extensión inválida, borrado), cierre comercial, vendedor registra su PQR |
| `tests/test_radicados.py` | 8 PQR simultáneos reciben radicados únicos |

Convenciones (ver `tests/conftest.py`):

- Fixtures: `client` (sin sesión), `admin` (sesión de admin, usa `ADMIN_PASS`), `pqr` (crea un PQR y lo borra al terminar).
- Los tests **nunca envían correo real**: un fixture automático reemplaza los envíos.
- Cada test debe limpiar lo que crea (fixtures con `yield` o `try/finally`).
- Nombre de datos de prueba con prefijo `TEST-` para reconocerlos si algo queda en la base.

## Lint

`ruff` (configurado en `pyproject.toml`, líneas de hasta 110 caracteres, reglas E, F, W, I, B).
`ruff check . --fix` corrige imports y espacios automáticamente.

## Cómo agregar…

### Un endpoint
1. Si necesita datos nuevos, agregue la función SQL en `app/repos/<dominio>.py` (usa `get_db_cursor()`).
2. Agregue la ruta en el Blueprint correspondiente de `app/rutas/` con su decorador de acceso
   (`@sesion_requerida` o `@rol_requerido(...)`). **Nunca deje una ruta sin decorador.**
3. Si es un área nueva: cree `app/rutas/<area>.py` con `bp = Blueprint("<area>", __name__)` y agréguelo a la lista en `app/rutas/__init__.py`.
4. Escriba un test y documente el endpoint en [api.md](api.md).

### Una columna o tabla
1. Edite `SCHEMA_SQL` en `app/db.py` (para bases nuevas).
2. Para bases **existentes** agregue una migración idempotente en `asegurar_tablas()` (`ALTER TABLE ...` comprobando antes
   en `information_schema`; ejemplo: `_migrar_notificar`). `CREATE TABLE IF NOT EXISTS` no modifica tablas ya creadas.
3. En MySQL 8, las columnas `TEXT`/`JSON` no admiten `DEFAULT ''`; use `DEFAULT ('')`.

### Un rol
Constantes y agrupaciones (`ROLES_VER_TODO`, `ROLES_COMERCIAL`…) en `app/seguridad.py`; agréguelo también a `ROLES_VALIDOS`.

### Una variable de entorno
Léala en `app/config.py` (o el módulo que la use), agréguela a `.env.example`, a `render.yaml` si aplica y a la tabla de
[ejecucion.md](ejecucion.md).

## Buenas prácticas del proyecto

- SQL siempre parametrizado (`cursor.execute(sql, (valores,))`); nunca concatenar datos del usuario.
- Datos del usuario autenticado (rol, id, línea) se toman de `session`, no del cuerpo de la petición.
- Cualquier valor que llegue del cliente y se use en rutas de archivos se valida con `RADICADO_RE` u otra lista blanca.
- No commitear `.env`, bases de datos (`*.xlsx` de datos), logs ni archivos subidos: están en `.gitignore`.
- Cambios de comportamiento → test primero (o junto con el cambio).

## Deuda técnica conocida

- `app/templates/index.html` concentra toda la interfaz (~4.500 líneas con CSS y JS en línea). Separar en archivos estáticos sería el siguiente paso de mantenibilidad.
- Sin migraciones versionadas (Alembic sería el paso natural si el esquema crece).
- Sin endpoint de descarga de evidencias ni de edición de PQR ya registrados.
- Límite de intentos de login en memoria por proceso.
