# API

Todas las rutas devuelven JSON. Salvo `POST /api/login`, exigen sesión (cookie). Sin sesión responden **401**; con sesión
pero sin el rol necesario, **403**. Los errores de validación devuelven **400** con `{"ok": false, "mensaje": "..."}`.

## Roles

| Rol | Puede |
|---|---|
| `ADMIN` | Todo (supera cualquier control de rol) |
| `LIDER_CALIDAD` | Dashboard y lista de PQR, investigación (Calidad), cambiar estado, eliminar PQR, listar/crear usuarios y editar credenciales (no las de un ADMIN) |
| `LIDER_COMERCIAL`, `COORDINADORA COMERCIAL`, `DIRECTORA COMERCIAL`, `COMERCIAL` | Dashboard y lista de PQR (lectura) y sección de seguimiento comercial |
| `DIRECTOR DE PRODUCCION` | Dashboard y lista de PQR (lectura) |
| `VENDEDOR` | Registrar PQR, consultar y adjuntar evidencias **solo a sus PQR** |

## Endpoints

| Método y ruta | Acceso | Descripción |
|---|---|---|
| `POST /api/login` | público (5 fallos/5 min → 429) | Inicia sesión. Cuerpo `{"usuario", "contrasena"}`. Devuelve `{"ok", "usuario": {...}}` |
| `POST /api/logout` | — | Cierra la sesión |
| `GET /api/sesion` | sesión | Datos del usuario actual (`401` si no hay sesión) |
| `GET /api/usuarios` | ADMIN, LIDER_CALIDAD | Lista de usuarios (nunca incluye el hash de la contraseña) |
| `POST /api/usuarios` | ADMIN, LIDER_CALIDAD | Crea un usuario (`nombre`, `usuario`, `contrasena`, `rol`, `documento`, `linea_producto`, `empresa`, `correo`, `telefono`) |
| `PUT /api/usuarios/<id>` | ADMIN | Edición completa (incluye rol y activo) |
| `DELETE /api/usuarios/<id>` | ADMIN | Elimina un usuario (el `admin` principal no se puede eliminar) |
| `PUT /api/usuarios/<id>/credenciales` | ADMIN, LIDER_CALIDAD | Cambia solo usuario y contraseña; LIDER_CALIDAD no puede tocar cuentas ADMIN |
| `GET /api/catalogo/productos?linea=&referencia_siesa=` | sesión | Busca productos. `linea` ∈ `INAPEL`, `MARFIL`, `TOROFIL` |
| `POST /api/catalogo/recargar` | ADMIN | Relee el catálogo desde el Excel |
| `POST /api/pqr` | sesión | Registra un PQR (ver abajo). Devuelve `radicado` y el resultado del correo |
| `GET /api/pqr/todos` | ver todo (ADMIN, calidad, comerciales, producción) | Lista todos los PQR |
| `GET /api/consultar/<valor>` | sesión (vendedor: solo suyos) | Busca por radicado, cliente o NIT; incluye investigación e historial. `404` si no existe |
| `DELETE /api/pqr/<radicado>` | ADMIN, LIDER_CALIDAD | Elimina el PQR, su historial, investigación y evidencias. `404` si no existe |
| `POST /api/seguimiento/calidad` | ADMIN, LIDER_CALIDAD | Guarda la sección de Calidad |
| `POST /api/seguimiento/comercial` | ADMIN y roles comerciales | Guarda la sección comercial |
| `POST /api/seguimiento` | ADMIN, calidad, comerciales | Ruta general anterior (compatibilidad); aplica según el rol |
| `POST /api/cambiar_estado` | ADMIN, LIDER_CALIDAD | `{"radicado", "estado"}`; registra el cambio en el historial. `404` si el PQR no existe |
| `GET /api/dashboard` | ver todo | `{"total", "estados": {...}, "tipos": {...}, "prioridades": {...}}` |
| `POST /api/evidencias` | sesión (vendedor: solo suyos) | Multipart: `radicado`, `tipo`, `archivos` (uno o varios) |
| `GET /healthz` | público | `{"ok": true}` si la base responde; `503` si no |
| `GET /` | público | Interfaz web |

### `POST /api/pqr`

Campos principales del cuerpo JSON:

| Campo | Descripción |
|---|---|
| `cliente`, `nit`, `contacto`, `tel`, `email` | Datos del cliente (`email` válido → se envía la confirmación) |
| `tipoSol` | Tipo de solicitud (petición, queja, reclamo…) |
| `prioridad`, `desc`, `expectativa` | Prioridad, descripción y expectativa del cliente |
| `productos` | Lista; cada elemento debe coincidir con el catálogo (`linea`, `referencia_siesa`, `detalle_presentacion`, `producto`, `unidad`) |
| `fechaRec`, `horaRec`, `ciudadRec`, `dptoRec`, `medio`, `otroMedio` | Datos de la recepción |

El vendedor, línea, empresa y datos del receptor se completan **desde la sesión**; lo que envíe el navegador se ignora.
El PQR siempre se guarda primero; si el correo falla, la respuesta lo indica (`email_estado`) pero el registro se mantiene.

Respuesta: `{"ok": true, "radicado": "PQR-2026-0001", "email_enviado": bool, "email_estado": "...", "email_mensaje": "...", "mensaje": "..."}`.

### Seguimiento

Sección **Calidad**: `resp`, `cargo`, `causa`, `herramientas` (lista; valores permitidos:
`5 ¿Por qué?`, `Diagrama Ishikawa`, `Análisis Pareto`, `Inspección visual`, `Ensayos de laboratorio`,
`Comparación muestra patrón`, `Checklist de inspección`), `deptos`, `respuesta_calidad`.

Sección **Comercial**: `acc`, `notif` (`Sí`/`No`), `fResp`, `cierre` (`Sí`/`No`), `fCierre`, `respuesta_comercial`.

Cada rol solo puede modificar su sección; intentar cambiar campos de la otra devuelve 403. Las fechas vacías se guardan como nulas.
Guardar Calidad por primera vez avisa por correo a los usuarios comerciales (una sola vez por PQR).

## Estados del PQR

```
Recibido → Radicado → En revisión → En investigación → Pendiente de información → Pendiente de decisión
        → Acción en proceso → Respuesta enviada → Cerrado   (o No procede)
```

Cambios automáticos: guardar la investigación deja el PQR en **En investigación**, o en **Cerrado** si `cierre` es `Sí`.
Los demás cambios se hacen a mano con `POST /api/cambiar_estado`. Cada cambio queda en el historial.
