import os
import json
import hashlib
import logging
import time
from datetime import datetime
from contextlib import contextmanager

import mysql.connector as mysql_connector
from mysql.connector import Error, pooling

logger = logging.getLogger(__name__)

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
# Configuración de conexión MySQL (variables de entorno)
# -------------------------------------------------------------------------

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "sistema_pqr")


# -------------------------------------------------------------------------
# Context managers para conexiones y cursores
# -------------------------------------------------------------------------

_POOL = None


def _pool():
    global _POOL
    if _POOL is None:
        _POOL = pooling.MySQLConnectionPool(
            pool_name="pqr",
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "8")),
            pool_reset_session=True,
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            connection_timeout=10,
        )
    return _POOL


@contextmanager
def get_db_connection():
    try:
        conn = _pool().get_connection()
    except Error:
        logger.exception("Error de conexión MySQL")
        raise
    try:
        yield conn
    finally:
        conn.close()  # devuelve la conexión al pool


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor(dictionary=True)
            yield cursor
            if commit:
                conn.commit()
        except Error as e:
            if conn.is_connected():
                conn.rollback()
            raise
        finally:
            cursor.close()


# -------------------------------------------------------------------------
# Esquema de tablas (ejecutar una sola vez al iniciar)
# -------------------------------------------------------------------------

SCHEMA_SQL = [
    # Tabla usuarios
    """CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        usuario VARCHAR(80) UNIQUE NOT NULL,
        contrasena_hash VARCHAR(255) NOT NULL,
        rol VARCHAR(50) NOT NULL,
        linea_producto VARCHAR(50) DEFAULT '',
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        activo TINYINT(1) DEFAULT 1,
        fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        documento VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        telefono VARCHAR(20) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla PQR
    """CREATE TABLE IF NOT EXISTS pqr (
        radicado VARCHAR(25) PRIMARY KEY,
        fecha DATETIME NOT NULL,
        hora TIME NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        cliente VARCHAR(150) DEFAULT '',
        nit VARCHAR(20) DEFAULT '',
        contacto VARCHAR(150) DEFAULT '',
        telefono VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        estado VARCHAR(50) DEFAULT 'Recibido',
        prioridad VARCHAR(50) DEFAULT '',
        descripcion TEXT DEFAULT (''),
        expectativa TEXT DEFAULT (''),
        productos JSON DEFAULT ('[]'),
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        vendedor VARCHAR(150) DEFAULT '',
        linea VARCHAR(50) DEFAULT '',
        usuario_id INT DEFAULT 0,
        correo_confirmacion_enviado TINYINT(1) DEFAULT 0,
        documento_receptor VARCHAR(20) DEFAULT '',
        correo_receptor VARCHAR(120) DEFAULT '',
        telefono_receptor VARCHAR(20) DEFAULT '',
        cargo_receptor VARCHAR(50) DEFAULT '',
        area_receptor VARCHAR(50) DEFAULT '',
        ciudad_recepcion VARCHAR(100) DEFAULT '',
        departamento_recepcion VARCHAR(100) DEFAULT '',
        medio_recepcion VARCHAR(50) DEFAULT '',
        otro_medio_recepcion VARCHAR(100) DEFAULT ''
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Historial
    """CREATE TABLE IF NOT EXISTS historial (
        id INT AUTO_INCREMENT PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        estado VARCHAR(50) NOT NULL,
        usuario VARCHAR(150) NOT NULL,
        fecha DATE NOT NULL,
        hora TIME NOT NULL,
        observacion TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Investigaciones
    """CREATE TABLE IF NOT EXISTS investigaciones (
        radicado VARCHAR(25) PRIMARY KEY,
        responsable VARCHAR(150) DEFAULT '',
        cargo VARCHAR(100) DEFAULT '',
        herramienta TEXT DEFAULT (''),
        causa TEXT DEFAULT (''),
        accion TEXT DEFAULT (''),
        notificar TINYINT(1) DEFAULT 0,
        fecha_respuesta DATE,
        fecha_cierre DATE,
        cierre VARCHAR(10) DEFAULT 'No',
        respuesta TEXT DEFAULT (''),
        departamentos TEXT DEFAULT (''),
        calidad_estado VARCHAR(50) DEFAULT 'pendiente',
        comercial_estado VARCHAR(50) DEFAULT 'pendiente',
        notificacion_comercial_enviada TINYINT(1) DEFAULT 0,
        respuesta_calidad TEXT DEFAULT (''),
        respuesta_comercial TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
    # Tabla Adjuntos
    """CREATE TABLE IF NOT EXISTS adjuntos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        archivo_original VARCHAR(255) NOT NULL,
        ruta_archivo VARCHAR(500) NOT NULL,
        fecha DATE,
        hora TIME,
        usuario VARCHAR(150) DEFAULT '',
        observacion TEXT DEFAULT (''),
        INDEX idx_radicado (radicado)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;"""
]


# -------------------------------------------------------------------------
# Inicializar tablas al importar
# -------------------------------------------------------------------------

def asegurar_tablas(intentos=30, espera=2):
    """Crea las tablas; espera a que MySQL acepte conexiones (arranque en docker)."""
    for intento in range(1, intentos + 1):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            break
        except Error:
            if intento == intentos:
                raise
            logger.warning("MySQL no disponible (%s/%s), reintentando...", intento, intentos)
            time.sleep(espera)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for sql in SCHEMA_SQL:
            cursor.execute(sql)
        conn.commit()
    logger.info("Tablas MySQL aseguradas correctamente.")


# -------------------------------------------------------------------------
# Helper: hashing de contraseñas (Werkzeug scrypt)
# -------------------------------------------------------------------------

def hash_contrasena(contrasena):
    from werkzeug.security import generate_password_hash
    return generate_password_hash(contrasena)


def verificar_contrasena(contrasena, hash_almacenado):
    from werkzeug.security import check_password_hash
    return check_password_hash(hash_almacenado, contrasena)


# -------------------------------------------------------------------------
# Usuarios
# -------------------------------------------------------------------------

def listar_usuarios():
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, fecha_creacion, documento, correo, telefono "
            "FROM usuarios ORDER BY nombre"
        )
        return cursor.fetchall()


def autenticar_usuario(usuario, contrasena):
    """Autentica un usuario verificando credenciales y activo."""
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, fecha_creacion, documento, correo, telefono "
            "FROM usuarios WHERE usuario = %s", (usuario,)
        )
        row = cursor.fetchone()

    if not row:
        return {"error": "Credenciales incorrectas."}

    # Verificar que el usuario esté activo
    if row['activo'] != 1:
        return {"error": "Usuario inactivo. Contacte al administrador."}

    # Verificar contraseña
    from werkzeug.security import check_password_hash
    if not check_password_hash(row['contrasena_hash'], contrasena):
        return {"error": "Credenciales incorrectas."}

    # Retornar datos del usuario
    usuario_data = {
        "id": row['id'],
        "usuario": row['usuario'],
        "nombre": row['nombre'],
        "rol": row['rol'],
        "linea_producto": row['linea_producto'],
        "empresa": row['empresa'],
        "activo": bool(row['activo']),
        "documento": row['documento'] or "",
        "correo": row['correo'] or "",
        "telefono": row['telefono'] or ""
    }
    return usuario_data


def obtener_usuario_por_id(uid):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, fecha_creacion, documento, correo, telefono "
            "FROM usuarios WHERE id = %s", (uid,)
        )
        return cursor.fetchone()


def obtener_usuario_por_documento(documento):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, fecha_creacion, documento, correo, telefono "
            "FROM usuarios WHERE documento = %s", (documento,)
        )
        return cursor.fetchone()


def _existe_usuario(usuario):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as cnt FROM usuarios WHERE usuario = %s", (usuario,))
        row = cursor.fetchone()
        return row['cnt'] > 0


def _existe_documento(documento, excepto_uid=None):
    with get_db_cursor() as cursor:
        if excepto_uid is not None:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM usuarios WHERE documento = %s AND id != %s",
                (documento, excepto_uid)
            )
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM usuarios WHERE documento = %s", (documento,))
        row = cursor.fetchone()
        return row['cnt'] > 0


def _existe_correo(correo, excepto_uid=None):
    with get_db_cursor() as cursor:
        if excepto_uid is not None:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM usuarios WHERE correo = %s AND id != %s",
                (correo, excepto_uid)
            )
        else:
            cursor.execute("SELECT COUNT(*) as cnt FROM usuarios WHERE correo = %s", (correo,))
        row = cursor.fetchone()
        return row['cnt'] > 0


def usuario_disponible(usuario, excepto_uid=None):
    return not _existe_usuario(usuario) if excepto_uid is None else not _existe_usuario_con_exclusion(usuario, excepto_uid)


def _existe_usuario_con_exclusion(usuario, excepto_uid):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM usuarios WHERE usuario = %s AND id != %s",
            (usuario, excepto_uid)
        )
        row = cursor.fetchone()
        return row['cnt'] > 0


def correo_disponible(correo, excepto_uid=None):
    return not _existe_correo(correo) if excepto_uid is None else not _existe_correo_con_exclusion(correo, excepto_uid)


def _existe_correo_con_exclusion(correo, excepto_uid):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM usuarios WHERE correo = %s AND id != %s",
            (correo, excepto_uid)
        )
        row = cursor.fetchone()
        return row['cnt'] > 0


def crear_usuario(nombre, usuario, contrasena, rol, documento="", linea_producto="", empresa="INAPEL", activo=True, correo="", telefono=""):
    if _existe_usuario(usuario):
        return {"ok": False, "mensaje": "El usuario ya existe."}
    if documento and _existe_documento(documento):
        return {"ok": False, "mensaje": "El documento ya está registrado."}
    if correo and _existe_correo(correo):
        return {"ok": False, "mensaje": "El correo electrónico ya está registrado."}
    if rol not in ("ADMIN", "VENDEDOR", "LIDER_CALIDAD", "LIDER_COMERCIAL",
                   "COORDINADORA_COMERCIAL", "DIRECTORA_COMERCIAL", "COMERCIAL", "DIRECTOR_DE_PRODUCCION"):
        return {"ok": False, "mensaje": "Rol inválido."}
    if rol == "VENDEDOR" and linea_producto not in ("INAPEL", "TOROFIL", ""):
        return {"ok": False, "mensaje": "Línea de producto inválida. Use INAPEL o TOROFIL."}

    hash_pw = hash_contrasena(contrasena)
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO usuarios (nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, documento, correo, telefono) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nombre, usuario, hash_pw, rol,
             linea_producto.upper() if linea_producto else "",
             empresa, 1 if activo else 0, documento, correo, telefono)
        )
        user_id = cursor.lastrowid
    return {"ok": True, "id": user_id, "mensaje": "Usuario creado correctamente."}


def actualizar_usuario(uid, **campos):
    with get_db_cursor() as cursor:
        # Buscar usuario
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (uid,))
        if not cursor.fetchone():
            return {"ok": False, "mensaje": "Usuario no encontrado."}

        # Construir update dinámico
        allowed = {"nombre", "usuario", "contrasena", "rol", "linea_producto", "empresa", "activo",
                   "documento", "correo", "telefono"}
        set_parts = []
        values = []

        if "nombre" in campos:
            set_parts.append("nombre = %s")
            values.append(str(campos["nombre"]).strip())
        if "usuario" in campos:
            u = str(campos["usuario"]).strip()
            if len(u) < 3:
                return {"ok": False, "mensaje": "El nombre de usuario debe tener al menos 3 caracteres."}
            import re
            if not re.match(r"^[A-Za-z0-9._@-]+$", u):
                return {"ok": False, "mensaje": "El nombre de usuario solo puede contener letras, números y los símbolos . _ @ -"}
            if _existe_usuario_con_exclusion(u, uid):
                return {"ok": False, "mensaje": "El nombre de usuario ya está en uso."}
            set_parts.append("usuario = %s")
            values.append(u)
        if "contrasena" in campos and campos["contrasena"]:
            set_parts.append("contrasena_hash = %s")
            values.append(hash_contrasena(str(campos["contrasena"])))
        if "rol" in campos:
            r = str(campos["rol"]).strip().upper()
            if r not in ("ADMIN", "VENDEDOR", "LIDER_CALIDAD", "LIDER_COMERCIAL",
                         "COORDINADORA_COMERCIAL", "DIRECTORA_COMERCIAL", "COMERCIAL", "DIRECTOR_DE_PRODUCCION"):
                return {"ok": False, "mensaje": "Rol inválido."}
            set_parts.append("rol = %s")
            values.append(r)
        if "linea_producto" in campos:
            l = str(campos["linea_producto"]).strip().upper()
            set_parts.append("linea_producto = %s")
            values.append(l if l in ("INAPEL", "TOROFIL", "") else "")
        if "empresa" in campos:
            e = str(campos["empresa"]).strip() or "INAPEL"
            set_parts.append("empresa = %s")
            values.append(e)
        if "activo" in campos:
            set_parts.append("activo = %s")
            values.append(1 if bool(campos["activo"]) else 0)
        if "documento" in campos:
            d = str(campos["documento"]).strip()
            set_parts.append("documento = %s")
            values.append(d)
        if "correo" in campos:
            c = str(campos["correo"]).strip()
            import re
            if c and not re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$", c):
                return {"ok": False, "mensaje": "Ingrese un correo electrónico válido."}
            if _existe_correo_con_exclusion(c, uid):
                return {"ok": False, "mensaje": "El correo electrónico ya está registrado."}
            set_parts.append("correo = %s")
            values.append(c)
        if "telefono" in campos:
            t = str(campos["telefono"]).strip()
            set_parts.append("telefono = %s")
            values.append(t)

        if not set_parts:
            return {"ok": False, "mensaje": "No hay campos para actualizar."}

        values.append(uid)
        query = f"UPDATE usuarios SET {', '.join(set_parts)} WHERE id = %s"
        cursor.execute(query, values)

    return {"ok": True, "mensaje": "Usuario actualizado correctamente."}


def desactivar_usuario(uid):
    return actualizar_usuario(uid, activo=False)


def eliminar_usuario(uid):
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        affected = cursor.rowcount
    if affected == 0:
        return {"ok": False, "mensaje": "Usuario no encontrado."}
    return {"ok": True, "mensaje": "Usuario eliminado correctamente."}


# -------------------------------------------------------------------------
# PQR
# -------------------------------------------------------------------------

def generar_radicado():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT radicado FROM pqr ORDER BY radicado DESC LIMIT 1")
        row = cursor.fetchone()
    if row and row['radicado']:
        try:
            partes = str(row['radicado']).split("-")
            if len(partes) >= 2:
                anio = int(partes[1])
                concat = int(partes[2])
                consecutivo = concat + 1
            else:
                consecutivo = 1
        except (ValueError, IndexError):
            consecutivo = 1
    else:
        consecutivo = 1
    from datetime import datetime
    anio_actual = datetime.now().year
    return f"PQR-{anio_actual}-{consecutivo:04d}"


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
    radicado = generar_radicado()
    datos["radicado"] = radicado

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

    rol_usuario = datos.get("rol_usuario", "")
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

    with get_db_cursor(commit=True) as cursor:
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

    with get_db_cursor(commit=True) as cursor:
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
    import shutil
    import os as os_mod
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM pqr WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM historial WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM investigaciones WHERE radicado = %s", (radicado,))
        cursor.execute("DELETE FROM adjuntos WHERE radicado = %s", (radicado,))
    carpeta = os_mod.path.join("Base_Datos", "Evidencias", str(radicado))
    if os_mod.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)
    return True

# -------------------------------------------------------------------------
# Semilla de usuarios
# -------------------------------------------------------------------------

def sembrar_usuarios():
    """Crea el admin (ADMIN_PASS) y los usuarios de usuarios_iniciales.py si no existen."""

    if not _existe_usuario("admin"):
        clave = os.getenv("ADMIN_PASS")
        if not clave:
            raise RuntimeError(
                "ADMIN_PASS debe configurarse antes de crear el administrador inicial."
            )
        crear_usuario(
            nombre="Administrador General",
            usuario="admin",
            contrasena=clave,
            rol="ADMIN",
            empresa="INAPEL",
        )

    try:
        from usuarios_iniciales import USUARIOS_INICIALES
    except ImportError:
        return

    for u in USUARIOS_INICIALES:
        usuario_login = str(u.get("usuario", "")).strip()
        if not usuario_login or _existe_usuario(usuario_login):
            continue
        crear_usuario(
            nombre=str(u.get("nombre", "")).strip(),
            usuario=usuario_login,
            contrasena=os.getenv("SEED_USER_PASSWORD") or str(u.get("contrasena", "")),
            rol=str(u.get("rol", "")).strip().upper(),
            documento=str(u.get("documento", "")).strip(),
            linea_producto=str(u.get("linea_producto", "")).strip().upper(),
            empresa=str(u.get("empresa", "") or "INAPEL").strip().upper(),
            activo=u.get("activo", True),
        )
