import os

from mysql_db import (
    listar_usuarios,
    autenticar_usuario,
    crear_usuario,
    actualizar_usuario,
    desactivar_usuario,
    eliminar_usuario,
    obtener_usuario_por_id,
    obtener_usuario_por_documento,
    usuario_disponible,
    correo_disponible,
    _existe_usuario,
    _existe_documento,
    _existe_correo,
)

# ==========================================================
# FUNCIONES DE DISPONIBILIDAD (usando mysql_db)
# ==========================================================

def documento_disponible(documento, excepto_uid=None):
    """Verifica que el documento no esté registrado."""
    return not _existe_documento(documento, excepto_uid)

# ==========================================================
# ROLES - Definidos localmente (mismo conjunto que routes.py)
# ==========================================================

ADMIN = "ADMIN"
VENDEDOR = "VENDEDOR"
LIDER_CALIDAD = "LIDER_CALIDAD"
LIDER_COMERCIAL = "LIDER_COMERCIAL"
COORDINADORA_COMERCIAL = "COORDINADORA COMERCIAL"
DIRECTORA_COMERCIAL = "DIRECTORA COMERCIAL"
COMERCIAL = "COMERCIAL"
DIRECTOR_PRODUCCION = "DIRECTOR DE PRODUCCION"

ROLES_VALIDOS = (
    ADMIN,
    VENDEDOR,
    LIDER_CALIDAD,
    LIDER_COMERCIAL,
    COORDINADORA_COMERCIAL,
    DIRECTORA_COMERCIAL,
    COMERCIAL,
    DIRECTOR_PRODUCCION
)

# ==========================================================
# AUTENTICACIÓN
# ==========================================================

# Reexportado desde mysql_db.py - verifica credenciales contra MySQL.

# ==========================================================
# LISTAR USUARIOS
# ==========================================================

# Reexportado desde mysql_db.py - lista todos los usuarios de MySQL.

# ==========================================================
# OBTENER USUARIO POR ID / DOCUMENTO
# ==========================================================

# Reexportado desde mysql_db.py - obtiene usuario por ID o documento.

# ==========================================================
# VERIFICAR DISPONIBILIDAD
# ==========================================================

# Reexportado desde mysql_db.py - verifica disponibilidad de usuario/documento/correo.

# ==========================================================
# ACTUALIZAR / DESACTIVAR / ELIMINAR USUARIOS
# ==========================================================

# Reexportado desde mysql_db.py - funciones de gestión de usuarios.

# ==========================================================
# SEMBRAR USUARIOS AL INICIAR
# ==========================================================

def sembrar_usuarios():
    """
    Crea el administrador general y los usuarios iniciales usando MySQL.
    La contraseña del administrador se obtiene de la variable de entorno ADMIN_PASS.
    """

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
            rol=ADMIN,
            linea_producto="",
            empresa="INAPEL",
            activo=True
        )

    try:
        from usuarios_iniciales import USUARIOS_INICIALES
    except ImportError:
        USUARIOS_INICIALES = []

    for u in USUARIOS_INICIALES:

        usuario_login = str(u.get("usuario", "")).strip()

        if not usuario_login:
            continue

        if _existe_usuario(usuario_login):
            continue

        crear_usuario(
            nombre=str(u.get("nombre", "")).strip(),
            usuario=usuario_login,
            contrasena=str(u.get("contrasena", "")),
            rol=str(u.get("rol", "")).strip().upper(),
            documento=str(u.get("documento", "")).strip(),
            linea_producto=str(u.get("linea_producto", "")).strip().upper(),
            empresa=str(u.get("empresa", "") or "INAPEL").strip().upper(),
            activo=u.get("activo", True)
        )