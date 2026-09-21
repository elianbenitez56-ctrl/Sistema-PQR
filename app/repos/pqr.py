import json
from contextlib import contextmanager
from datetime import datetime

from app.db import get_db_connection, get_db_cursor

HERRAMIENTAS_ANALISIS = (
    "5 ¿Por qué?",
    "Diagrama Ishikawa",
    "Análisis Pareto",
    "Inspección visual",
    "Ensayos de laboratorio",
    "Comparación muestra patrón",
    "Checklist de inspección"
)


# -------------------------------------------------------------------------
# PQR
# -------------------------------------------------------------------------

@contextmanager
def _radicado_bloqueado():
    """Cursor con lock nombrado de MySQL: serializa generar radicado + insertar (entre hilos y procesos).

    Usa una sola conexión (el pool no se agota esperando el lock) y confirma o revierte al salir.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT GET_LOCK('pqr_radicado', 10) AS ok")
            if cursor.fetchone()["ok"] != 1:
                raise RuntimeError("No fue posible obtener el bloqueo para generar el radicado.")
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.execute("SELECT RELEASE_LOCK('pqr_radicado')")
                cursor.fetchone()
        finally:
            cursor.close()


def _siguiente_radicado(cursor):
    cursor.execute(
        "SELECT radicado FROM pqr "
        "ORDER BY CAST(SUBSTRING_INDEX(radicado, '-', -1) AS UNSIGNED) DESC LIMIT 1"
    )
    row = cursor.fetchone()
    consecutivo = 1
    if row and row['radicado']:
        try:
            consecutivo = int(str(row['radicado']).split("-")[2]) + 1
        except (ValueError, IndexError):
            pass
    return f"PQR-{datetime.now().year}-{consecutivo:04d}"


def consultar_pqr(valor_busqueda):
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

        # Obtener información de investigación
        inv = obtener_investigacion_radicado(row['radicado'])

        # Obtener historial
        hist = obtener_historial_radicado(row['radicado'])

        # Formatear productos
        try:
            productos = json.loads(row['productos']) if row['productos'] else []
        except (TypeError, ValueError):
            productos = []

        result = {
            "radicado": row['radicado'],
            "fechaRec": str(row['fecha']),
            "horaRec": str(row['hora']),
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
            "investigacion": inv,
            "historial": hist,
            "savedAt": f"{row['fecha']}T{row['hora']}"
        }
        return result


def listar_pqrs():
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT p.*, u.nombre as usuario_nombre "
            "FROM pqr p LEFT JOIN usuarios u ON p.usuario_id = u.id"
        )
        rows = cursor.fetchall()

    lista = []
    for row in rows:
        try:
            productos = json.loads(row['productos']) if row['productos'] else []
        except (TypeError, ValueError):
            productos = []

        lista.append({
            "radicado": row['radicado'],
            "fechaRec": str(row['fecha']),
            "horaRec": str(row['hora']),
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
            "savedAt": f"{row['fecha']}T{row['hora']}" if row['hora'] else row['fecha']
        })
    return lista


def guardar_pqr(datos):
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
                fecha_rec if isinstance(fecha_rec, datetime) else datetime.now(),
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
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE pqr SET estado = %s WHERE radicado = %s",
            (estado, radicado)
        )
        if cursor.rowcount == 0:
            return False
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO historial (radicado, estado, usuario, fecha, hora, observacion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (radicado, estado, "Sistema",
             datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"),
             "Estado actualizado")
        )
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


def guardar_investigacion(datos, calidad_estado=None, comercial_estado=None,
                        notificacion_comercial_enviada=None):
    radicado = datos.get("radicado", "")
    estado_calidad = str(
        calidad_estado if calidad_estado is not None else "pendiente"
    ).strip().lower()
    estado_comercial = str(
        comercial_estado if comercial_estado is not None else "pendiente"
    ).strip().lower()
    aviso_enviado = bool(
        notificacion_comercial_enviada
    ) if notificacion_comercial_enviada is not None else False

    herramientas = normalizar_herramientas(
        datos.get("herramientas", datos.get("herr", ""))
    )
    herramientas_str = serializar_herramientas(herramientas)

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT radicado FROM investigaciones WHERE radicado = %s", (radicado,)
        )
        existe = cursor.fetchone()

    valores = [
        radicado,
        datos.get("resp", ""),
        datos.get("cargo", ""),
        herramientas_str,
        datos.get("causa", ""),
        datos.get("acc", ""),
        datos.get("notif", ""),
        datos.get("fResp", ""),
        datos.get("fCierre", ""),
        datos.get("cierre", ""),
        datos.get("respTxt", ""),
        datos.get("deptos", "")
    ]
    respuesta_calidad = datos.get("respuesta_calidad", "")
    respuesta_comercial = datos.get("respuesta_comercial", "")

    with get_db_cursor(commit=True) as cursor:
        if existe:
            cursor.execute(
                "UPDATE investigaciones SET responsable = %s, cargo = %s, herramienta = %s, "
                "causa = %s, accion = %s, notificar = %s, fecha_respuesta = %s, "
                "fecha_cierre = %s, cierre = %s, respuesta = %s, "
                "departamentos = %s, calidad_estado = %s, comercial_estado = %s, "
                "notificacion_comercial_enviada = %s, respuesta_calidad = %s, "
                "respuesta_comercial = %s WHERE radicado = %s",
                (*valores, estado_calidad, estado_comercial,
                 1 if aviso_enviado else 0, respuesta_calidad, respuesta_comercial, radicado)
            )
        else:
            cursor.execute(
                "INSERT INTO investigaciones (radicado, responsable, cargo, herramienta, "
                "causa, accion, notificar, fecha_respuesta, fecha_cierre, cierre, "
                "respuesta, departamentos, calidad_estado, comercial_estado, "
                "notificacion_comercial_enviada, respuesta_calidad, respuesta_comercial) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (*valores, estado_calidad, estado_comercial,
                 1 if aviso_enviado else 0, respuesta_calidad, respuesta_comercial)
            )

    # Auto-transition de estado del PQR
    cierre = datos.get("cierre", "No")
    nuevo_estado = "Cerrado" if cierre == "Sí" else "En investigación"
    actualizar_estado_pqr(radicado, nuevo_estado)

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO historial (radicado, estado, usuario, fecha, hora, observacion) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (radicado, nuevo_estado, "Sistema",
             datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"),
             "Seguimiento actualizado")
        )

    return {
        "calidad_estado": estado_calidad,
        "comercial_estado": estado_comercial,
        "notificacion_comercial_enviada": aviso_enviado
    }


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


def eliminar_adjunto(id_Adjunto):
    with get_db_cursor() as cursor:
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

def normalizar_herramientas(valor):
    if isinstance(valor, list):
        valores = valor
    else:
        texto = str(valor or "").strip()
        if not texto:
            return []
        try:
            valores = json.loads(texto) if texto.startswith("[") else [texto]
        except (TypeError, ValueError):
            valores = [texto]
    return [str(item).strip() for item in valores if str(item or "").strip()]


def serializar_herramientas(herramientas):
    valores = normalizar_herramientas(herramientas)
    if len(valores) <= 1:
        return valores[0] if valores else ""
    return json.dumps(valores, ensure_ascii=False)


# -------------------------------------------------------------------------
# Eliminar PQR
# -------------------------------------------------------------------------

def eliminar_pqr(radicado):
    import os as os_mod
    import shutil
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM pqr WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM historial WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM investigaciones WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM adjuntos WHERE radicado = %s", (radicado,))
    carpeta = os_mod.path.join("Base_Datos", "Evidencias", str(radicado))
    if os_mod.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)
    return True
