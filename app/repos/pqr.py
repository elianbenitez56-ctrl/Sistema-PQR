import json
import re
from contextlib import contextmanager
from datetime import datetime

from psycopg.rows import dict_row

from app.db import Error, get_db_connection, get_db_cursor
from app.dominio import normalizar_herramientas, serializar_herramientas

# -------------------------------------------------------------------------
# PQR
# -------------------------------------------------------------------------

@contextmanager
def _radicado_bloqueado():
    """Cursor con advisory lock de PostgreSQL, con ámbito de transacción: serializa generar
    radicado + insertar (entre procesos), y se libera solo al hacer commit o rollback.

    Usa una sola conexión (el pool no se agota esperando el lock).
    """
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET LOCAL statement_timeout = '10s'")
            try:
                cursor.execute("SELECT pg_advisory_xact_lock(hashtext('pqr_radicado'))")
            except Error as error:
                conn.rollback()
                raise RuntimeError("No fue posible obtener el bloqueo para generar el radicado.") from error
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise


def _siguiente_radicado(cursor):
    anio = datetime.now().year
    cursor.execute(
        "SELECT radicado FROM pqr WHERE split_part(radicado, '-', 2) = %s "
        "ORDER BY CAST(split_part(radicado, '-', 3) AS INTEGER) DESC LIMIT 1",
        (str(anio),)
    )
    row = cursor.fetchone()
    consecutivo = 1
    if row and row['radicado']:
        try:
            consecutivo = int(str(row['radicado']).split("-")[2]) + 1
        except (ValueError, IndexError):
            pass
    return f"PQR-{anio}-{consecutivo:04d}"


def _fila_a_pqr(row):
    try:
        productos = json.loads(row['productos']) if row['productos'] else []
    except (TypeError, ValueError):
        productos = []

    fecha_str = row['fecha'].strftime("%Y-%m-%d") if hasattr(row['fecha'], "strftime") else str(row['fecha'])
    hora_str = str(row['hora']) if row['hora'] else ""

    return {
        "radicado": row['radicado'],
        "fechaRec": fecha_str,
        "horaRec": hora_str,
        "tipoSol": row['tipo'] or "",
        "cliente": row['cliente'] or "",
        "nit": row['nit'] or "",
        "contacto": row['contacto'] or "",
        "tel": row['telefono'] or "",
        "email": row['correo'] or "",
        "estado": row['estado'] or "Recibido",
        "prioridad": row['prioridad'] or "",
        "desc": row['descripcion'] or "",
        "expectativa": row['expectativa'] or "",
        "productos": productos,
        "empresa": row['empresa'] or "INAPEL",
        "vendedor": row['vendedor'] or "",
        "linea": row['linea'] or "",
        "usuario_id": row['usuario_id'] or 0,
        "documento_receptor": row['documento_receptor'] or "",
        "correo_receptor": row['correo_receptor'] or "",
        "telefono_receptor": row['telefono_receptor'] or "",
        "cargo_receptor": row['cargo_receptor'] or "",
        "area_receptor": row['area_receptor'] or "",
        "ciudad_recepcion": row['ciudad_recepcion'] or "",
        "departamento_recepcion": row['departamento_recepcion'] or "",
        "medio_recepcion": row['medio_recepcion'] or "",
        "otro_medio_recepcion": row['otro_medio_recepcion'] or "",
        "savedAt": f"{fecha_str}T{hora_str}" if hora_str else fecha_str,
    }


def consultar_pqr(valor_busqueda):
    """Busca por radicado, cliente o NIT. Devuelve el PQR con su investigación e historial, o None."""
    valor = str(valor_busqueda).strip().upper()
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT p.*, u.nombre as usuario_nombre "
            "FROM pqr p LEFT JOIN usuarios u ON p.usuario_id = u.id "
            "WHERE UPPER(p.radicado) = %s OR UPPER(p.cliente) = %s OR UPPER(p.nit) = %s",
            (valor, valor, valor)
        )
        row = cursor.fetchone()
    if not row:
        return None

    pqr = _fila_a_pqr(row)
    pqr["investigacion"] = obtener_investigacion_radicado(row['radicado'])
    pqr["historial"] = obtener_historial_radicado(row['radicado'])
    pqr["adjuntos"] = [
        {
            "id": a["id"],
            "nombre": a["archivo_original"],
            "tipo": a["tipo"] or "",
            "fecha": str(a["fecha"]) if a["fecha"] else "",
        }
        for a in listar_adjuntos(row['radicado'])
    ]
    return pqr


def consultar_pqr_publico(radicado):
    """Consulta reducida para la vista pública (enlace del correo, sin sesión).

    A diferencia de `consultar_pqr`, busca solo por radicado exacto (no por
    cliente/NIT) y devuelve únicamente campos seguros para el cliente externo:
    nada de causa raíz, responsable interno, departamentos ni adjuntos.
    """
    valor = str(radicado).strip().upper()
    with get_db_cursor() as cursor:
        cursor.execute("SELECT p.* FROM pqr p WHERE UPPER(p.radicado) = %s", (valor,))
        row = cursor.fetchone()
    if not row:
        return None

    pqr = _fila_a_pqr(row)
    inv = obtener_investigacion_radicado(row['radicado']) or {}
    hist = obtener_historial_radicado(row['radicado'])
    return {
        "radicado": pqr["radicado"],
        "cliente": pqr.get("cliente", ""),
        "tipoSol": pqr.get("tipoSol", ""),
        "estado": pqr.get("estado", ""),
        "fechaRec": pqr.get("fechaRec", ""),
        "desc": pqr.get("desc", ""),
        "historial": [
            {"estado": h["estado"], "fecha": h["fecha"], "hora": h["hora"]}
            for h in hist
        ],
        "respuesta_comercial": inv.get("respuesta_comercial") or "",
        "cerrado": inv.get("cierre") == "Sí",
    }


def listar_pqrs():
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT p.*, u.nombre as usuario_nombre "
            "FROM pqr p LEFT JOIN usuarios u ON p.usuario_id = u.id"
        )
        rows = cursor.fetchall()
    return [_fila_a_pqr(row) for row in rows]


def crear_pqr(datos):
    """Inserta el PQR (y su primer historial) con un radicado nuevo, que queda en datos["radicado"]."""
    fecha_rec = datos.get("fechaRec")
    hora_rec = datos.get("horaRec")
    if isinstance(fecha_rec, str):
        pass
    elif fecha_rec is None:
        fecha_rec = datetime.now()
    if isinstance(hora_rec, str):
        pass
    elif hora_rec is None:
        hora_rec = datetime.now().strftime("%H:%M:%S")

    usuario_id = datos.get("usuario_id", 0)
    vendedor = datos.get("vendedor", "")
    linea = datos.get("linea", "")
    empresa = datos.get("empresa", "INAPEL")
    documento_receptor = datos.get("documento_receptor", "")
    correo_receptor = datos.get("correo_receptor", "")
    telefono_receptor = datos.get("telefono_receptor", "")
    cargo_receptor = datos.get("cargo_receptor", "")
    area_receptor = datos.get("area_receptor", "")
    ciudad_rec = datos.get("ciudadRec", "")
    dpto_rec = datos.get("dptoRec", "")
    medio = datos.get("medio", "")
    otro_medio = datos.get("otroMedio", "")

    productos_json = json.dumps(datos.get("productos", []), ensure_ascii=False)

    with _radicado_bloqueado() as cursor:
        radicado = _siguiente_radicado(cursor)
        datos["radicado"] = radicado

        cursor.execute(
            "INSERT INTO pqr "
            "(radicado, fecha, hora, tipo, cliente, nit, contacto, telefono, correo, "
            "estado, prioridad, descripcion, expectativa, productos, empresa, vendedor, "
            "linea, usuario_id, correo_confirmacion_enviado, documento_receptor, "
            "correo_receptor, telefono_receptor, cargo_receptor, area_receptor, "
            "ciudad_recepcion, departamento_recepcion, medio_recepcion, otro_medio_recepcion) "
            "VALUES "
            "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                radicado,
                fecha_rec if isinstance(fecha_rec, str) else datetime.now(),
                hora_rec if isinstance(hora_rec, str) else datetime.now().strftime("%H:%M:%S"),
                datos.get("tipoSol", ""),
                datos.get("cliente", ""),
                datos.get("nit", ""),
                datos.get("contacto", ""),
                datos.get("tel", ""),
                datos.get("email", ""),
                datos.get("estado", "Recibido"),
                datos.get("prioridad", ""),
                datos.get("desc", ""),
                datos.get("expectativa", ""),
                productos_json,
                empresa,
                vendedor,
                linea,
                usuario_id,
                datos.get("correo_confirmacion_enviado", 0),
                documento_receptor,
                correo_receptor,
                telefono_receptor,
                cargo_receptor,
                area_receptor,
                ciudad_rec,
                dpto_rec,
                medio,
                otro_medio
            )
        )

        cursor.execute(
            "INSERT INTO historial (radicado, estado, usuario, fecha, hora, observacion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (radicado, datos.get("estado", "Recibido"), "Sistema",
             datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"),
             "PQR registrado")
        )

    return True


def actualizar_estado_pqr(radicado, estado):
    """Cambia el estado. El historial lo registra quien llama (guardar_historial / guardar_investigacion)."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE pqr SET estado = %s WHERE radicado = %s",
            (estado, radicado)
        )
        if cursor.rowcount == 0:
            return False
    return True


# -------------------------------------------------------------------------
# Investigaciones
# -------------------------------------------------------------------------

def obtener_investigacion_radicado(radicado):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM investigaciones WHERE radicado = %s", (radicado,)
        )
        row = cursor.fetchone()
    if not row:
        return {
            "resp": "", "cargo": "", "herr": "", "herramientas": [],
            "causa": "Materias primas", "acc": "Reposición",
            "notif": "Sí", "fResp": "", "fCierre": "", "cierre": "No",
            "respuesta_calidad": "", "respuesta_comercial": "",
            "deptos": "", "calidad_estado": "pendiente",
            "comercial_estado": "pendiente", "notificacion_comercial_enviada": False
        }
    return {
        "resp": row['responsable'] or "",
        "cargo": row['cargo'] or "",
        "herr": row['herramienta'] or "",
        "herramientas": normalizar_herramientas(row['herramienta']),
        "causa": row['causa'] or "",
        "acc": row['accion'] or "",
        "notif": row['notificar'] if row['notificar'] else "",
        "fResp": row['fecha_respuesta'] or "",
        "fCierre": row['fecha_cierre'] or "",
        "cierre": row['cierre'] or "No",
        "respuesta_calidad": row['respuesta_calidad'] or "",
        "respuesta_comercial": row['respuesta_comercial'] or "",
        "deptos": row['departamentos'] or "",
        "calidad_estado": str(row['calidad_estado'] or "pendiente").strip().lower(),
        "comercial_estado": str(row['comercial_estado'] or "pendiente").strip().lower(),
        "notificacion_comercial_enviada": bool(row['notificacion_comercial_enviada'])
    }


def obtener_historial_radicado(radicado):
    """Obtiene el historial de estado de una PQR."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, estado, usuario, fecha, hora, observacion "
            "FROM historial WHERE radicado = %s ORDER BY id ASC",
            (radicado,)
        )
        rows = cursor.fetchall()

    if not rows:
        return []

    return [
        {
            "id": row['id'],
            "estado": row['estado'],
            "usuario": row['usuario'],
            "fecha": str(row['fecha']),
            "hora": str(row['hora']),
            "observacion": row['observacion'] or ""
        }
        for row in rows
    ]


def guardar_historial(radicado, estado, usuario="Sistema", observacion=""):
    """Guarda una entrada en el historial de una PQR."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO historial (radicado, estado, usuario, fecha, hora, observacion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (radicado, estado, usuario,
             datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"),
             observacion)
        )


def guardar_investigacion(radicado, datos, calidad_estado, comercial_estado, aviso_enviado):
    """Inserta o actualiza la investigación del PQR. No decide estados ni escribe historial."""
    valores = [
        datos.get("resp", ""),
        datos.get("cargo", ""),
        serializar_herramientas(datos.get("herramientas", datos.get("herr", ""))),
        datos.get("causa", ""),
        datos.get("acc", ""),
        datos.get("notif", ""),
        datos.get("fResp") or None,
        datos.get("fCierre") or None,
        datos.get("cierre", ""),
        datos.get("respTxt", ""),
        datos.get("deptos", ""),
        calidad_estado,
        comercial_estado,
        1 if aviso_enviado else 0,
        datos.get("respuesta_calidad", ""),
        datos.get("respuesta_comercial", ""),
    ]

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT radicado FROM investigaciones WHERE radicado = %s", (radicado,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE investigaciones SET responsable = %s, cargo = %s, herramienta = %s, "
                "causa = %s, accion = %s, notificar = %s, fecha_respuesta = %s, "
                "fecha_cierre = %s, cierre = %s, respuesta = %s, "
                "departamentos = %s, calidad_estado = %s, comercial_estado = %s, "
                "notificacion_comercial_enviada = %s, respuesta_calidad = %s, "
                "respuesta_comercial = %s WHERE radicado = %s",
                (*valores, radicado)
            )
        else:
            cursor.execute(
                "INSERT INTO investigaciones (responsable, cargo, herramienta, "
                "causa, accion, notificar, fecha_respuesta, fecha_cierre, cierre, "
                "respuesta, departamentos, calidad_estado, comercial_estado, "
                "notificacion_comercial_enviada, respuesta_calidad, respuesta_comercial, radicado) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (*valores, radicado)
            )


def marcar_correo_confirmacion(radicado, enviado):
    """Actualiza la columna correo_confirmacion_enviado en la tabla pqr."""
    valor = 1 if enviado else 0
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE pqr SET correo_confirmacion_enviado = %s WHERE radicado = %s",
            (valor, radicado)
        )
    return True


def correo_confirmacion_enviado(radicado):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT correo_confirmacion_enviado FROM pqr WHERE radicado = %s",
            (radicado,)
        )
        fila = cursor.fetchone()
    return bool(fila and fila["correo_confirmacion_enviado"])


def marcar_notificacion_comercial_enviada(radicado):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE investigaciones SET notificacion_comercial_enviada = 1 WHERE radicado = %s",
            (radicado,)
        )
    return True


# -------------------------------------------------------------------------
# Adjuntos
# -------------------------------------------------------------------------

def guardar_adjunto(radicado, tipo, archivo_original, ruta_archivo,
                    observacion="", usuario="Cliente"):
    ahora = datetime.now()
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO adjuntos (radicado, tipo, archivo_original, ruta_archivo, "
            "fecha, hora, usuario, observacion) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (radicado, tipo, archivo_original, ruta_archivo,
             ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M:%S"), usuario, observacion)
        )
    return True


def listar_adjuntos(radicado):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM adjuntos WHERE radicado = %s ORDER BY id DESC", (radicado,)
        )
        return cursor.fetchall()


def obtener_adjunto(id_adjunto):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM adjuntos WHERE id = %s", (id_adjunto,))
        return cursor.fetchone()


def eliminar_adjunto(id_Adjunto):
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM adjuntos WHERE id = %s", (id_Adjunto,))
        affected = cursor.rowcount
    return affected > 0


# -------------------------------------------------------------------------
# Dashboard
# -------------------------------------------------------------------------

def obtener_dashboard():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT estado, COUNT(*) as cnt FROM pqr GROUP BY estado")
        estados = {row['estado']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT tipo, COUNT(*) as cnt FROM pqr GROUP BY tipo")
        tipos = {row['tipo']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT prioridad, COUNT(*) as cnt FROM pqr GROUP BY prioridad")
        prioridades = {row['prioridad']: row['cnt'] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) as total FROM pqr")
        total = cursor.fetchone()['total']

    return {
        "total": total,
        "estados": estados,
        "tipos": tipos,
        "prioridades": prioridades
    }


# -------------------------------------------------------------------------
# Normalizador de herramientas
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# Eliminar PQR
# -------------------------------------------------------------------------

RADICADO_RE = re.compile(r"PQR-\d{4}-\d{4,}")


def eliminar_pqr(radicado):
    """Elimina de la base de datos el PQR y sus registros asociados (historial, investigación,
    adjuntos). Los archivos de evidencia en el almacenamiento los borra la capa de servicios.
    Devuelve True, o "not_found" si no existía.
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM pqr WHERE radicado = %s", (radicado,))
        existia = cursor.rowcount > 0
        cursor.execute("DELETE FROM historial WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM investigaciones WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM adjuntos WHERE radicado = %s", (radicado,))
    return True if existia else "not_found"
