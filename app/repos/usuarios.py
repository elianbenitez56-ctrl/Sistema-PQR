import os

from werkzeug.security import generate_password_hash

from app.db import get_db_cursor

# `contrasena_hash` solo sale de aquí para autenticar; el resto de consultas no lo exponen.
CAMPOS_PUBLICOS = (
    "id, nombre, usuario, rol, linea_producto, empresa, activo, fecha_creacion, documento, correo, telefono"
)


def listar_usuarios():
    with get_db_cursor() as cursor:
        cursor.execute(f"SELECT {CAMPOS_PUBLICOS} FROM usuarios ORDER BY nombre")
        return cursor.fetchall()


def obtener_usuario_por_id(uid):
    with get_db_cursor() as cursor:
        cursor.execute(f"SELECT {CAMPOS_PUBLICOS} FROM usuarios WHERE id = %s", (uid,))
        return cursor.fetchone()


def obtener_usuario_con_hash(usuario):
    """Usuario por nombre de acceso, incluido `contrasena_hash` (solo para autenticar)."""
    with get_db_cursor() as cursor:
        cursor.execute(f"SELECT {CAMPOS_PUBLICOS}, contrasena_hash FROM usuarios WHERE usuario = %s", (usuario,))
        return cursor.fetchone()


def _ocupado(campo, valor, excepto_uid=None):
    sql = f"SELECT COUNT(*) AS cnt FROM usuarios WHERE {campo} = %s"
    params = [valor]
    if excepto_uid is not None:
        sql += " AND id != %s"
        params.append(excepto_uid)
    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()["cnt"] > 0


def usuario_disponible(usuario, excepto_uid=None):
    return not _ocupado("usuario", usuario, excepto_uid)


def documento_disponible(documento, excepto_uid=None):
    return not _ocupado("documento", documento, excepto_uid)


def correo_disponible(correo, excepto_uid=None):
    return not _ocupado("correo", correo, excepto_uid)


def crear_usuario(nombre, usuario, contrasena, rol, documento="", linea_producto="", empresa="INAPEL",
                  activo=True, correo="", telefono=""):
    """Inserta el usuario y devuelve su id. Las validaciones son del servicio."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO usuarios (nombre, usuario, contrasena_hash, rol, linea_producto, "
            "empresa, activo, documento, correo, telefono) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (nombre, usuario, generate_password_hash(contrasena), rol, linea_producto,
             empresa, 1 if activo else 0, documento, correo, telefono)
        )
        return cursor.lastrowid


def actualizar_usuario(uid, **campos):
    """Actualiza solo los campos indicados. Devuelve False si el usuario no existe."""
    columnas = {
        "nombre": "nombre", "usuario": "usuario", "rol": "rol", "linea_producto": "linea_producto",
        "empresa": "empresa", "documento": "documento", "correo": "correo", "telefono": "telefono",
    }
    sets, valores = [], []
    for clave, columna in columnas.items():
        if clave in campos:
            sets.append(f"{columna} = %s")
            valores.append(campos[clave])
    if campos.get("contrasena"):
        sets.append("contrasena_hash = %s")
        valores.append(generate_password_hash(campos["contrasena"]))
    if "activo" in campos:
        sets.append("activo = %s")
        valores.append(1 if campos["activo"] else 0)

    with get_db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (uid,))
        if not cursor.fetchone():
            return False
        if sets:
            cursor.execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s", (*valores, uid))
    return True


def eliminar_usuario(uid):
    """True si existía y se eliminó."""
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (uid,))
        return cursor.rowcount > 0


def sembrar_usuarios():
    """Crea el admin (ADMIN_PASS) y los usuarios de semillas.py que aún no existan."""

    if usuario_disponible("admin"):
        clave = os.getenv("ADMIN_PASS")
        if not clave:
            raise RuntimeError(
                "ADMIN_PASS debe configurarse antes de crear el administrador inicial."
            )
        crear_usuario(nombre="Administrador General", usuario="admin", contrasena=clave, rol="ADMIN")

    from app.semillas import USUARIOS_INICIALES

    for u in USUARIOS_INICIALES:
        usuario_login = str(u.get("usuario", "")).strip()
        if not usuario_login or not usuario_disponible(usuario_login):
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
