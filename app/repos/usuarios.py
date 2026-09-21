import os

from app.db import get_db_cursor


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


def documento_disponible(documento, excepto_uid=None):
    return not _existe_documento(documento, excepto_uid)


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
        from app.semillas import USUARIOS_INICIALES
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
