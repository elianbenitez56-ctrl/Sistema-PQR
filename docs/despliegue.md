# Despliegue y operación (Render + Supabase/Neon)

El servicio se define en `render.yaml` (blueprint) y se construye desde el `Dockerfile`.

## Componentes

| Componente | Dónde | Notas |
|---|---|---|
| Aplicación web | Render, servicio `sistema-pqr` (runtime Docker) | gunicorn, 2 workers × 4 hilos, health check en `/healthz`. `TZ=<-05>5` fijo en el `Dockerfile` (hora de Colombia) |
| Base de datos | **PostgreSQL externo** (Render no ofrece Postgres gratis en este plan) | Supabase, Neon o cualquier Postgres 14+ accesible desde Render |
| Evidencias | **Supabase Storage** (`SUPABASE_URL`/`SUPABASE_SERVICE_KEY`) | Sin esas variables cae al disco local, que en Render se pierde en cada deploy sin plan de pago; ver abajo |
| Correo | **API HTTPS de Brevo** (`BREVO_API_KEY`) | Render bloquea los puertos SMTP salientes en todos sus planes; SMTP clásico (`SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD`) solo sirve en local/Docker |

## Primer despliegue

1. **Cree el proyecto en Supabase o Neon** y copie los datos de conexión (host, puerto, usuario, contraseña,
   nombre de la base). Ambos exigen TLS: use `PGSSLMODE=require`. La aplicación crea las tablas sola al arrancar.
2. En Render: **New → Blueprint** y seleccione el repositorio. Se crea el servicio con `render.yaml`.
3. Complete las variables marcadas como *sync: false* en el panel:

   | Variable | Valor |
   |---|---|
   | `ADMIN_PASS` | Contraseña inicial de `admin` (larga y única) |
   | `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | Los del connection string de Supabase/Neon (`PGPORT` ya tiene valor en el blueprint) |
   | `BREVO_API_KEY`, `SMTP_FROM` | Cuenta gratis en [Brevo](https://app.brevo.com) (SMTP & API → API Keys) con el remitente verificado |
   | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Del proyecto Supabase, con un bucket **privado** llamado `evidencias` creado de antemano (Storage → New bucket) |
   | `SEED_USER_PASSWORD` | Contraseña inicial de los usuarios sembrados (recomendado) |

   `SECRET_KEY` se genera automáticamente (`generateValue: true`); **no la cambie** después o se cerrarán todas las sesiones y se invalidarán los enlaces de consulta pública (`/consulta-pqr/<radicado>`) ya enviados por correo.
   Ajuste `PQR_URL_BASE` si el dominio no es `https://sistema-pqr.onrender.com`.
4. Espere a que el health check quede en verde y entre con `admin`.
5. Cambie las contraseñas temporales de los usuarios sembrados.

## Evidencias persistentes

Con `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` configuradas, las evidencias se suben al bucket privado `evidencias` de
Supabase Storage y persisten entre despliegues. Sin esas variables, se guardan en el disco local del contenedor:
en Render (todos los planes, sin disco montado) el sistema de archivos se reinicia en cada despliegue y
**las evidencias subidas se pierden** (la base de datos no se ve afectada). Alternativa de pago: en `render.yaml`
descomente el bloque `disk` (exige plan de pago y limita el servicio a una sola instancia).

## Operación

- **Despliegues:** cada push a `main` despliega (si el auto-deploy está activo). Pruebe antes con `docker compose -f docker-compose.yml up --build`.
- **Esquema:** los cambios se aplican solos al arrancar (ver `asegurar_tablas`). No hay paso manual de migración.
- **Copias de seguridad:** Supabase y Neon respaldan automáticamente (revise el plan contratado: retención y *point-in-time recovery*
  varían). Las evidencias del disco de Render se respaldan con *Disk Snapshots*.
- **Logs:** panel de Render → *Logs*. Los correos fallidos y errores de catálogo aparecen ahí.
- **Escalado:** el límite de intentos de login es por proceso, y el disco persistente restringe a una instancia. Cada proceso abre
  hasta `PG_POOL_SIZE` (16) conexiones: con 2 workers, hasta 32; verifique el límite de conexiones de su plan en Supabase/Neon
  (los planes gratuitos suelen limitarlo bajo — considere el *connection pooler* que ambos ofrecen si lo alcanza).
- **Rotar credenciales:** cambie la variable en Render y reinicie. Rotar `SECRET_KEY` cierra todas las sesiones.

## Lista de comprobación antes de abrir a usuarios

- [ ] `SECRET_KEY` generada por Render; `ADMIN_PASS` y `SEED_USER_PASSWORD` fuertes.
- [ ] Base Postgres (Supabase/Neon) con `PGSSLMODE=require` y acceso restringido cuando el proveedor lo permita.
- [ ] `BREVO_API_KEY` configurada y remitente (`SMTP_FROM`) verificado en Brevo.
- [ ] Bucket privado `evidencias` creado en Supabase Storage y `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` configuradas (o aceptada la pérdida de evidencias sin ellas).
- [ ] `PQR_URL_BASE` con el dominio real (los correos enlazan a él).
- [ ] Contraseñas temporales de los usuarios sembrados cambiadas.
