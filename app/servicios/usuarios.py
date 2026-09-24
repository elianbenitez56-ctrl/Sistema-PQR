"""Casos de uso de usuarios: autenticación, alta, edición, credenciales y baja."""
import re

from werkzeug.security import check_password_hash

from app.errores import ErrorNegocio
from app.repos.usuarios import (
    actualizar_usuario,
    correo_disponible,
    crear_usuario,
    documento_disponible,
    eliminar_usuario,
    obtener_usuario_con_hash,
    obtener_usuario_por_id,
    usuario_disponible,
)
from app.seguridad import ADMIN, LIDER_CALIDAD, ROLES_VALIDOS, VENDEDOR
from app.validaciones import validar_correo, validar_telefono

ADMIN_PRINCIPAL = "admin"
LINEAS_USUARIO = ("INAPEL", "TOROFIL", "")
USUARIO_RE = re.compile(r"^[A-Za-z0-9._@-]+$")


# ---------------------------------------------------------- validaciones

def _texto(valor):
    return str(valor).strip()


def _validar_rol(rol):
    if rol not in ROLES_VALIDOS:
        raise ErrorNegocio(
            "Rol inválido. Use VENDEDOR, LIDER_CALIDAD, LIDER_COMERCIAL, COORDINADORA COMERCIAL, "
            "DIRECTORA COMERCIAL, COMERCIAL o DIRECTOR DE PRODUCCION."
        )


def _validar_linea(linea):
    if linea not in LINEAS_USUARIO:
        raise ErrorNegocio("Línea de producto inválida. Use INAPEL o TOROFIL.")


def _validar_nombre_usuario(usuario, excepto_uid=None):
    if len(usuario) < 3:
        raise ErrorNegocio("El nombre de usuario debe tener al menos 3 caracteres.")
    if not USUARIO_RE.match(usuario):
        raise ErrorNegocio("El nombre de usuario solo puede contener letras, números y los símbolos . _ @ -")
    if not usuario_disponible(usuario, excepto_uid=excepto_uid):
        raise ErrorNegocio("El nombre de usuario ya está en uso.")


def _validar_documento(documento, excepto_uid=None):
    if not documento:
        return
    if not documento.isdigit():
        raise ErrorNegocio("El documento solo puede contener números.")
    if not documento_disponible(documento, excepto_uid=excepto_uid):
        raise ErrorNegocio("El documento ya está registrado.")


def _validar_correo(correo, excepto_uid=None):
    if not correo:
        return
    if not validar_correo(correo):
        raise ErrorNegocio("Ingrese un correo electrónico válido.")
    if not correo_disponible(correo, excepto_uid=excepto_uid):
        raise ErrorNegocio("El correo electrónico ya está registrado.")


def _validar_telefono(telefono):
    if not telefono:
        return
    if not validar_telefono(telefono):
        raise ErrorNegocio("El teléfono solo puede contener números y los símbolos espacio - ( ) . +")
    if not 7 <= sum(ch.isdigit() for ch in telefono) <= 10:
        raise ErrorNegocio("El teléfono debe tener entre 7 y 10 dígitos.")


def _usuario_existente(uid):
    destino = obtener_usuario_por_id(uid)
    if not destino:
        raise ErrorNegocio("Usuario no encontrado.", 404)
    return destino


# ---------------------------------------------------------- casos de uso

def autenticar(usuario, contrasena):
    """Devuelve el usuario si las credenciales son válidas y está activo; si no, ErrorNegocio 401."""
    fila = obtener_usuario_con_hash(usuario)
    if not fila:
        raise ErrorNegocio("Credenciales incorrectas.", 401)
    if fila["activo"] != 1:
        raise ErrorNegocio("Usuario inactivo. Contacte al administrador.", 401)
    if not check_password_hash(fila["contrasena_hash"], contrasena):
        raise ErrorNegocio("Credenciales incorrectas.", 401)

    return {
        "id": fila["id"],
        "usuario": fila["usuario"],
        "nombre": fila["nombre"],
        "rol": fila["rol"],
        "linea_producto": fila["linea_producto"],
        "empresa": fila["empresa"],
        "activo": bool(fila["activo"]),
        "documento": fila["documento"] or "",
        "correo": fila["correo"] or "",
        "telefono": fila["telefono"] or "",
    }


def crear(datos, rol_actual=None):
    nombre = _texto(datos.get("nombre", ""))
    usuario = _texto(datos.get("usuario", ""))
    contrasena = str(datos.get("contrasena", ""))
    rol = _texto(datos.get("rol", "")).upper()
    documento = _texto(datos.get("documento", ""))
    linea = _texto(datos.get("linea_producto", "")).upper()
    correo = _texto(datos.get("correo", ""))
    telefono = _texto(datos.get("telefono", ""))

    if not nombre or not usuario or not contrasena:
        raise ErrorNegocio("Nombre, usuario y contraseña son obligatorios.")
    if len(contrasena) < 6:
        raise ErrorNegocio("La contraseña debe tener al menos 6 caracteres.")
    _validar_rol(rol)
    if rol == ADMIN and rol_actual == LIDER_CALIDAD:
        raise ErrorNegocio("No puede crear usuarios con rol ADMIN.", 403)
    if rol == VENDEDOR:
        _validar_linea(linea)
    _validar_documento(documento)
    _validar_correo(correo)
    _validar_telefono(telefono)
    if not usuario_disponible(usuario):
        raise ErrorNegocio("El usuario ya existe.")

    uid = crear_usuario(
        nombre=nombre, usuario=usuario, contrasena=contrasena, rol=rol, documento=documento,
        linea_producto=linea, empresa=_texto(datos.get("empresa", "") or "INAPEL").upper(),
        activo=datos.get("activo", True), correo=correo, telefono=telefono,
    )
    return {"ok": True, "id": uid, "mensaje": "Usuario creado correctamente."}


def actualizar(uid, datos):
    campos = {}

    if "nombre" in datos:
        campos["nombre"] = _texto(datos["nombre"])
    if "usuario" in datos:
        campos["usuario"] = _texto(datos["usuario"])
        _validar_nombre_usuario(campos["usuario"], uid)
    if datos.get("contrasena"):
        campos["contrasena"] = str(datos["contrasena"])
    if "rol" in datos:
        campos["rol"] = _texto(datos["rol"]).upper()
        _validar_rol(campos["rol"])
    if "linea_producto" in datos:
        campos["linea_producto"] = _texto(datos["linea_producto"]).upper()
        _validar_linea(campos["linea_producto"])
    if "documento" in datos:
        campos["documento"] = _texto(datos["documento"])
        _validar_documento(campos["documento"], uid)
    if "correo" in datos:
        campos["correo"] = _texto(datos["correo"])
        _validar_correo(campos["correo"], uid)
    if "telefono" in datos:
        campos["telefono"] = _texto(datos["telefono"])
        _validar_telefono(campos["telefono"])
    if "activo" in datos:
        campos["activo"] = bool(datos["activo"])

    if not campos:
        raise ErrorNegocio("No hay campos para actualizar.")
    if not actualizar_usuario(uid, **campos):
        raise ErrorNegocio("Usuario no encontrado.", 404)
    return {"ok": True, "mensaje": "Usuario actualizado correctamente."}


def cambiar_credenciales(uid, datos, rol_actual):
    """Solo usuario y contraseña. LIDER_CALIDAD no puede tocar cuentas ADMIN."""
    destino = _usuario_existente(uid)
    if rol_actual == LIDER_CALIDAD and destino["rol"] == ADMIN:
        raise ErrorNegocio("No puede modificar las credenciales de usuarios administradores.", 403)

    usuario = _texto(datos.get("usuario", ""))
    contrasena = str(datos.get("contrasena", ""))
    if not usuario and not contrasena:
        raise ErrorNegocio("Debe indicar un nuevo usuario o una nueva contraseña.")

    campos = {}
    if usuario:
        _validar_nombre_usuario(usuario, uid)
        campos["usuario"] = usuario
    if contrasena:
        if len(contrasena) < 6:
            raise ErrorNegocio("La contraseña debe tener al menos 6 caracteres.")
        campos["contrasena"] = contrasena

    actualizar_usuario(uid, **campos)
    return {"ok": True, "mensaje": "Credenciales actualizadas correctamente."}


def eliminar(uid, uid_sesion):
    destino = _usuario_existente(uid)
    if _texto(destino.get("usuario", "")).lower() == ADMIN_PRINCIPAL:
        raise ErrorNegocio("No es posible eliminar el administrador principal del sistema.")
    if str(destino["id"]) == str(uid_sesion or "").strip():
        raise ErrorNegocio("No puede eliminar el usuario con el que inició sesión.")
    if not eliminar_usuario(uid):
        raise ErrorNegocio("Usuario no encontrado.", 500)
    return {"ok": True, "mensaje": "Usuario eliminado correctamente."}
