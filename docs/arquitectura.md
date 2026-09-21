# Arquitectura

## Visión general

Aplicación monolítica: un servidor Flask que sirve la interfaz (una sola página compuesta por `index.html` + parciales Jinja,
con CSS y JavaScript en `app/static/`) y una API JSON bajo `/api/*`. Los datos viven en MySQL y las evidencias en disco.

```
Navegador ──HTTP──▶ gunicorn ──▶ Flask (app/)
  (index.html)                     ├─ rutas/      HTTP: lee la petición, exige rol, llama a un servicio, arma el JSON
                                   ├─ servicios/  casos de uso y reglas: orquestan repos, correo y catálogo
                                   ├─ dominio.py  reglas puras (flujo de seguimiento, herramientas)
                                   ├─ repos/      SQL (único lugar que habla con la base)
                                   └─ db.py ──▶ MySQL 8 (pool de conexiones)
                                   └─ disco ──▶ PQR_UPLOAD_DIR/<radicado>/  (evidencias)
```

## Estructura del código

```
wsgi.py                     entrada: app = create_app()
app/
  __init__.py               create_app(): configura, crea esquema, siembra usuarios, carga catálogo,
                            registra blueprints y el manejador de ErrorNegocio, "/" y "/healthz"
  config.py                 variables de entorno -> Config
  db.py                     pool MySQL, get_db_cursor(), SCHEMA_SQL, asegurar_tablas() y migraciones
  errores.py                ErrorNegocio: error esperado con su código HTTP (se traduce a JSON en un solo lugar)
  seguridad.py              constantes de roles, rol_requerido(), sesion_requerida()
  validaciones.py           validadores de correo y teléfono
  dominio.py                reglas puras sin BD ni Flask (estados del seguimiento, campos obligatorios, herramientas)
  repos/usuarios.py         SQL de usuarios (nunca devuelve el hash salvo para autenticar)
  repos/pqr.py              SQL de PQR, historial, investigaciones, adjuntos y dashboard
  servicios/pqr.py          registrar (catálogo, receptor desde sesión, verificación, correo), consultar, cambiar estado, eliminar
  servicios/seguimiento.py  guardar seguimiento Calidad/Comercial (permisos por sección, estados, aviso a comercial)
  servicios/usuarios.py     autenticar, alta, edición, credenciales y baja con sus validaciones
  servicios/correo.py       envío de correos (confirmación al cliente, aviso a comercial)
  servicios/catalogo.py     catálogo maestro leído de datos/LISTADO PRODUCTOS.xlsx (en memoria, con recarga)
  rutas/                    un Blueprint por área: sesion, usuarios, catalogo, pqr, seguimiento, evidencias
  semillas.py               usuarios iniciales de INAPEL
  templates/index.html      esqueleto de la página (enlaza CSS/JS e incluye los parciales)
  templates/partials/       una vista por archivo: login, sidebar, topbar, panel_* (formulario, consultar,
                            basedatos, seguimiento, usuarios, dashboard) y modales
  static/css/               estilos por capa, en orden de cascada: base, layout, formulario, componentes,
                            pantallas, feedback, responsive, accesibilidad
  static/js/                scripts clásicos (comparten ámbito global) cargados en orden: nucleo, sesion, layout,
                            formulario, consultar, basedatos, usuarios, seguimiento, arranque (al final)
  static/img/, manifest.json  imágenes y manifiesto PWA
```

**Regla de dependencias:** `rutas → servicios → repos → db`, y `dominio` no depende de nada de la aplicación salvo roles/errores.
Las rutas no tienen lógica de negocio ni SQL; los servicios no conocen Flask ni HTTP (lanzan `ErrorNegocio`); los repos
solo hacen SQL y no toman decisiones de negocio.

**Errores:** un servicio lanza `ErrorNegocio(mensaje, status)` y `create_app` lo convierte en `{"ok": false, "mensaje": ...}`
con ese código HTTP (`extra` agrega campos como `faltantes`; `clave="error"` mantiene el formato `{"error": ...}` de `/api/consultar`).

## Ciclo de arranque (`create_app`)

1. Lee la configuración (`SECRET_KEY` es obligatoria salvo `FLASK_DEBUG=1`).
2. `asegurar_tablas()`: espera hasta 60 s a que MySQL responda, crea las tablas que falten y aplica migraciones.
3. `sembrar_usuarios()`: crea `admin` (con `ADMIN_PASS`) y los usuarios de `semillas.py` que no existan.
4. Carga el catálogo de productos. Si falla, la app arranca igual y el error queda en el log.
5. Registra los blueprints. `GET /healthz` hace `SELECT 1` y devuelve 200/503 (lo usan Docker y Render).

## Base de datos (MySQL 8, `utf8mb4`)

El esquema está en `app/db.py` (`SCHEMA_SQL`) y se crea solo. No hay herramienta de migraciones: los cambios
sobre tablas existentes se agregan como función en `asegurar_tablas()` (ver `_migrar_notificar`).

| Tabla | Contenido | Clave |
|---|---|---|
| `usuarios` | Cuentas: nombre, usuario, hash de contraseña (scrypt), rol, línea de producto, empresa, activo, documento, correo, teléfono | `id`; `usuario` único |
| `pqr` | El caso: datos del cliente, tipo, estado, prioridad, descripción, productos (JSON), datos de quien recibe, vendedor, línea, `usuario_id`, `correo_confirmacion_enviado` | `radicado` |
| `historial` | Una fila por cambio de estado (estado, usuario, fecha, hora, observación) | `id`; `radicado` |
| `investigaciones` | Una por PQR: sección de Calidad (responsable, causa, herramientas, departamentos, respuesta de calidad) y de Comercial (acciones, notificación, fechas, cierre, respuesta comercial), con `calidad_estado` / `comercial_estado` | `radicado` |
| `adjuntos` | Evidencias subidas: nombre original, ruta, tipo, usuario, fecha | `id`; `radicado` |

Las relaciones se hacen por `radicado` (sin claves foráneas); `eliminar_pqr()` borra las cuatro tablas y la carpeta de evidencias.

### Radicado

Formato `PQR-{año}-{consecutivo:04d}`, p. ej. `PQR-2026-0042`. El consecutivo es global (no se reinicia cada año).
Se genera dentro de `crear_pqr()` con un *lock* nombrado de MySQL (`GET_LOCK('pqr_radicado')`), de modo que la
generación y la inserción son atómicas incluso con varios procesos.

## Autenticación y autorización

- Login con usuario y contraseña (`POST /api/login`). Las contraseñas se guardan con hash Werkzeug (scrypt).
- Sesión en cookie firmada (`SECRET_KEY`), `HttpOnly`, `SameSite=Lax`, `Secure` fuera de desarrollo; dura 12 horas.
- **Límite de intentos:** 5 fallos por combinación IP + usuario en 5 minutos → HTTP 429. El contador está en
  memoria de cada proceso (con varios workers el límite efectivo es por proceso).
- Cada endpoint declara su acceso con `@sesion_requerida` (cualquier usuario autenticado) o `@rol_requerido(...)`.
  `ADMIN` pasa todos los controles de rol.
- Un **vendedor** solo puede consultar y adjuntar evidencias a PQR que él registró. Los datos del receptor
  (vendedor, línea, empresa, documento…) se toman siempre de la sesión, nunca del navegador.
- Lista completa de permisos: [api.md](api.md).

## Evidencias (archivos adjuntos)

`POST /api/evidencias` recibe archivos multipart para un radicado. Validaciones: radicado con formato
`PQR-AAAA-NNNN`, extensión permitida (imágenes, PDF, Office, txt/csv, mp4/mov), nombre saneado con
`secure_filename`, tamaño máximo de petición `MAX_UPLOAD_MB`. Se guardan en `PQR_UPLOAD_DIR/<radicado>/` y se
registran en `adjuntos`. **Aún no existe un endpoint para descargarlos.**

## Correo

`servicios/correo.py` usa SMTP (Gmail por defecto).

| Cuándo | A quién | Condición |
|---|---|---|
| Se registra un PQR | Correo del cliente | Correo válido y confirmación aún no enviada |
| Calidad completa su sección | Usuarios activos con rol comercial y correo registrado | Una sola vez por PQR (`notificacion_comercial_enviada`) |

El envío nunca bloquea el registro: el PQR se guarda primero y el resultado del correo se informa en la respuesta.

## Catálogo de productos

`datos/LISTADO PRODUCTOS.xlsx` se carga en memoria al arrancar. Líneas: `INAPEL`, `MARFIL`, `TOROFIL`. Al registrar un PQR,
cada producto enviado se valida contra el catálogo por línea y referencia SIESA. `POST /api/catalogo/recargar`
(ADMIN) relee el archivo sin reiniciar.

## Limitaciones conocidas

- Sin descarga de evidencias ni edición de un PQR ya registrado (solo estado y seguimiento).
- El límite de intentos de login es por proceso (ver arriba).
- Sin migraciones versionadas: los cambios de esquema sobre bases existentes se programan a mano.
- En Render sin disco persistente las evidencias se pierden en cada despliegue (ver [despliegue.md](despliegue.md)).
- Contraseña temporal compartida en `app/semillas.py`; use `SEED_USER_PASSWORD` y haga que cada usuario la cambie.
