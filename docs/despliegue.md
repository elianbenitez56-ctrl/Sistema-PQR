# Despliegue y operación (Render)

El servicio se define en `render.yaml` (blueprint) y se construye desde el `Dockerfile`.

## Componentes

| Componente | Dónde | Notas |
|---|---|---|
| Aplicación web | Render, servicio `sistema-pqr` (runtime Docker) | gunicorn, 2 workers × 4 hilos, health check en `/healthz` |
| Base de datos | **MySQL externo** (Render no ofrece MySQL gestionado) | Cualquier MySQL 8 accesible desde Render (Aiven, PlanetScale, un VPS, etc.) |
| Evidencias | Disco persistente de Render montado en `/data/evidencias` | Requiere plan de pago; ver abajo |
| Correo | Gmail SMTP | Contraseña de aplicación |

## Primer despliegue

1. **Cree la base MySQL** (`utf8mb4`) y un usuario con permisos sobre esa base (`CREATE`, `ALTER`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`). La aplicación crea las tablas sola.
2. En Render: **New → Blueprint** y seleccione el repositorio. Se crea el servicio con `render.yaml`.
3. Complete las variables marcadas como *sync: false* en el panel:

   | Variable | Valor |
   |---|---|
   | `ADMIN_PASS` | Contraseña inicial de `admin` (larga y única) |
   | `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` | Los de su base (`MYSQL_PORT`/`MYSQL_DATABASE` ya tienen valor en el blueprint) |
   | `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Cuenta de correo y contraseña de aplicación |
   | `SEED_USER_PASSWORD` | Contraseña inicial de los usuarios sembrados (recomendado) |

   `SECRET_KEY` se genera automáticamente (`generateValue: true`); **no la cambie** después o se cerrarán todas las sesiones.
   Ajuste `PQR_URL_BASE` si el dominio no es `https://sistema-pqr.onrender.com`.
4. Espere a que el health check quede en verde y entre con `admin`.
5. Cambie las contraseñas temporales de los usuarios sembrados.

## Evidencias persistentes

Sin disco, el sistema de archivos de Render se reinicia en cada despliegue y **las evidencias subidas se pierden**
(la base de datos no se ve afectada). Para conservarlas, en `render.yaml` descomente el bloque:

```yaml
disk:
  name: evidencias
  mountPath: /data/evidencias
  sizeGB: 5
```

Los discos exigen un plan de pago y limitan el servicio a una sola instancia.

## Operación

- **Despliegues:** cada push a `main` despliega (si el auto-deploy está activo). Pruebe antes con `docker compose -f docker-compose.yml up --build`.
- **Esquema:** los cambios se aplican solos al arrancar (ver `asegurar_tablas`). No hay paso manual de migración.
- **Copias de seguridad:** configure respaldos automáticos en el proveedor de MySQL. Las evidencias del disco de Render se respaldan con *Disk Snapshots*.
- **Logs:** panel de Render → *Logs*. Los correos fallidos y errores de catálogo aparecen ahí.
- **Escalado:** el límite de intentos de login es por proceso, y el disco persistente restringe a una instancia. Cada proceso abre hasta `MYSQL_POOL_SIZE` (16) conexiones: con 2 workers, hasta 32; verifique el `max_connections` de su MySQL.
- **Rotar credenciales:** cambie la variable en Render y reinicie. Rotar `SECRET_KEY` cierra todas las sesiones.

## Lista de comprobación antes de abrir a usuarios

- [ ] `SECRET_KEY` generada por Render; `ADMIN_PASS` y `SEED_USER_PASSWORD` fuertes.
- [ ] Base MySQL con respaldos y acceso restringido (idealmente solo desde Render).
- [ ] Contraseña de aplicación de Gmail propia (no compartida ni versionada).
- [ ] Disco de evidencias montado (o aceptada su pérdida).
- [ ] `PQR_URL_BASE` con el dominio real (los correos enlazan a él).
- [ ] Contraseñas temporales de los usuarios sembrados cambiadas.
