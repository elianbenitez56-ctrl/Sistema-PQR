import re
from flask import Blueprint, jsonify, request, session
from app.seguridad import (
    ADMIN,
    LIDER_CALIDAD,
    ROLES_VALIDOS,
    VENDEDOR,
    rol_requerido
)
from app.validaciones import validar_correo, validar_telefono
from app.repos.usuarios import (
    documento_disponible,
    actualizar_usuario,
    correo_disponible,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    obtener_usuario_por_id,
    usuario_disponible
)

bp = Blueprint("usuarios", __name__)


# ==========================================================
# ADMINISTRACIÓN DE USUARIOS
# ADMIN: gestión completa. LIDER_CALIDAD: solo credenciales.
# ==========================================================

@bp.route("/api/usuarios", methods=["GET"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_listar():

    return jsonify({
        "ok": True,
        "usuarios": listar_usuarios()
    })


@bp.route("/api/usuarios", methods=["POST"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_crear():

    datos = request.get_json(silent=True) or request.form or {}

    nombre = str(datos.get("nombre", "")).strip()
    usuario = str(datos.get("usuario", "")).strip()
    contrasena = str(datos.get("contrasena", ""))
    rol = str(datos.get("rol", "")).strip().upper()
    documento = str(datos.get("documento", "")).strip()
    linea = str(datos.get("linea_producto", "")).strip().upper()
    empresa = str(datos.get("empresa", "") or "INAPEL").strip().upper()
    activo = datos.get("activo", True)
    correo = str(datos.get("correo", "")).strip()
    telefono = str(datos.get("telefono", "")).strip()

    if not nombre or not usuario or not contrasena:
        return jsonify({
            "ok": False,
            "mensaje": "Nombre, usuario y contraseña son obligatorios."
        }), 400

    if rol not in ROLES_VALIDOS:
        return jsonify({
            "ok": False,
            "mensaje": "Rol inválido. Use VENDEDOR, LIDER_CALIDAD, LIDER_COMERCIAL, COORDINADORA COMERCIAL, DIRECTORA COMERCIAL, COMERCIAL o DIRECTOR DE PRODUCCION."
        }), 400

    if rol == VENDEDOR and linea not in ("INAPEL", "TOROFIL", ""):
        return jsonify({
            "ok": False,
            "mensaje": "Línea de producto inválida. Use INAPEL o TOROFIL."
        }), 400

    if documento:
        if not documento.isdigit():
            return jsonify({
                "ok": False,
                "mensaje": "El documento solo puede contener números."
            }), 400
        if not documento_disponible(documento):
            return jsonify({
                "ok": False,
                "mensaje": "El documento ya está registrado."
            }), 400

    if correo:
        if not validar_correo(correo):
            return jsonify({
                "ok": False,
                "mensaje": "Ingrese un correo electrónico válido."
            }), 400
        if not correo_disponible(correo):
            return jsonify({
                "ok": False,
                "mensaje": "El correo electrónico ya está registrado."
            }), 400

    if telefono:
        if not validar_telefono(telefono):
            return jsonify({
                "ok": False,
                "mensaje": "El teléfono solo puede contener números y los símbolos espacio - ( ) . +"
            }), 400
        digitos_tel = "".join(ch for ch in telefono if ch.isdigit())
        if len(digitos_tel) < 7 or len(digitos_tel) > 10:
            return jsonify({
                "ok": False,
                "mensaje": "El teléfono debe tener entre 7 y 10 dígitos."
            }), 400

    resultado = crear_usuario(
        nombre=nombre,
        usuario=usuario,
        contrasena=contrasena,
        rol=rol,
        documento=documento,
        linea_producto=linea,
        empresa=empresa,
        activo=activo,
        correo=correo,
        telefono=telefono
    )

    if not resultado["ok"]:
        return jsonify(resultado), 400

    return jsonify(resultado), 201


@bp.route("/api/usuarios/<int:uid>", methods=["PUT"])
@rol_requerido(ADMIN)
def api_usuarios_actualizar(uid):

    datos = request.get_json(silent=True) or request.form or {}

    campos = {}

    if "nombre" in datos:
        campos["nombre"] = str(datos["nombre"]).strip()
    if "usuario" in datos:
        usuario = str(datos["usuario"]).strip()
        if len(usuario) < 3:
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario debe tener al menos 3 caracteres."
            }), 400
        if not re.match(r"^[A-Za-z0-9._@-]+$", usuario):
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario solo puede contener letras, números y los símbolos . _ @ -"
            }), 400
        if not usuario_disponible(usuario, excepto_uid=uid):
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario ya está en uso."
            }), 400
        campos["usuario"] = usuario
    if datos.get("contrasena"):
        campos["contrasena"] = str(datos["contrasena"])
    if "rol" in datos:
        rol = str(datos["rol"]).strip().upper()
        if rol not in ROLES_VALIDOS:
            return jsonify({
                "ok": False,
                "mensaje": "Rol inválido. Use VENDEDOR, LIDER_CALIDAD, LIDER_COMERCIAL, COORDINADORA COMERCIAL, DIRECTORA COMERCIAL, COMERCIAL o DIRECTOR DE PRODUCCION."
            }), 400
        campos["rol"] = rol
    if "linea_producto" in datos:
        linea = str(datos["linea_producto"]).strip().upper()
        if linea not in ("INAPEL", "TOROFIL", ""):
            return jsonify({
                "ok": False,
                "mensaje": "Línea de producto inválida. Use INAPEL o TOROFIL."
            }), 400
        campos["linea_producto"] = linea
    if "documento" in datos:
        documento = str(datos["documento"]).strip()
        if documento and not documento.isdigit():
            return jsonify({
                "ok": False,
                "mensaje": "El documento solo puede contener números."
            }), 400
        if documento and not documento_disponible(documento, excepto_uid=uid):
            return jsonify({
                "ok": False,
                "mensaje": "El documento ya está registrado."
            }), 400
        campos["documento"] = documento
    if "correo" in datos:
        correo = str(datos["correo"]).strip()
        if correo and not validar_correo(correo):
            return jsonify({
                "ok": False,
                "mensaje": "Ingrese un correo electrónico válido."
            }), 400
        if correo and not correo_disponible(correo, excepto_uid=uid):
            return jsonify({
                "ok": False,
                "mensaje": "El correo electrónico ya está registrado."
            }), 400
        campos["correo"] = correo
    if "telefono" in datos:
        telefono = str(datos["telefono"]).strip()
        if telefono:
            if not validar_telefono(telefono):
                return jsonify({
                    "ok": False,
                    "mensaje": "El teléfono solo puede contener números y los símbolos espacio - ( ) . +"
                }), 400
            digitos_tel = "".join(ch for ch in telefono if ch.isdigit())
            if len(digitos_tel) < 7 or len(digitos_tel) > 10:
                return jsonify({
                    "ok": False,
                    "mensaje": "El teléfono debe tener entre 7 y 10 dígitos."
                }), 400
        campos["telefono"] = telefono
    if "activo" in datos:
        campos["activo"] = bool(datos["activo"])

    resultado = actualizar_usuario(uid, **campos)

    if not resultado["ok"]:
        return jsonify(resultado), 404

    return jsonify(resultado)


# Identificador del administrador principal del sistema,
# sembrado por sembrar_usuarios() en users_db.py.
ADMIN_PRINCIPAL = "admin"


@bp.route("/api/usuarios/<int:uid>", methods=["DELETE"])
@rol_requerido(ADMIN)
def api_usuarios_eliminar(uid):

    destino = obtener_usuario_por_id(uid)

    if not destino:
        return jsonify({
            "ok": False,
            "mensaje": "Usuario no encontrado."
        }), 404

    if str(destino.get("usuario", "")).strip().lower() == ADMIN_PRINCIPAL:
        return jsonify({
            "ok": False,
            "mensaje": "No es posible eliminar el administrador principal del sistema."
        }), 400

    if str(destino.get("id", "")).strip() == str(session.get("usuario_id", "")).strip():
        return jsonify({
            "ok": False,
            "mensaje": "No puede eliminar el usuario con el que inició sesión."
        }), 400

    resultado = eliminar_usuario(uid)

    if not resultado["ok"]:
        return jsonify(resultado), 500

    return jsonify({
        "ok": True,
        "mensaje": "Usuario eliminado correctamente."
    })


@bp.route("/api/usuarios/<int:uid>/credenciales", methods=["PUT"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_credenciales(uid):

    """
    Permite modificar ÚNICAMENTE el nombre de usuario y la contraseña.
    Documento, rol, empresa, línea de producto y permisos NO se tocan.
    El LIDER_CALIDAD no puede editar credenciales de usuarios ADMIN.
    """

    destino = obtener_usuario_por_id(uid)

    if not destino:
        return jsonify({
            "ok": False,
            "mensaje": "Usuario no encontrado."
        }), 404

    if session.get("rol") == LIDER_CALIDAD and destino["rol"] == ADMIN:
        return jsonify({
            "ok": False,
            "mensaje": "No puede modificar las credenciales de usuarios administradores."
        }), 403

    datos = request.get_json(silent=True) or request.form or {}

    usuario = str(datos.get("usuario", "")).strip()
    contrasena = str(datos.get("contrasena", ""))

    if not usuario and not contrasena:
        return jsonify({
            "ok": False,
            "mensaje": "Debe indicar un nuevo usuario o una nueva contraseña."
        }), 400

    campos = {}

    if usuario:
        if len(usuario) < 3:
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario debe tener al menos 3 caracteres."
            }), 400

        if not re.match(r"^[A-Za-z0-9._@-]+$", usuario):
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario solo puede contener letras, números y los símbolos . _ @ -"
            }), 400

        if not usuario_disponible(usuario, excepto_uid=uid):
            return jsonify({
                "ok": False,
                "mensaje": "El nombre de usuario ya está en uso."
            }), 400

        campos["usuario"] = usuario

    if contrasena:
        if len(contrasena) < 6:
            return jsonify({
                "ok": False,
                "mensaje": "La contraseña debe tener al menos 6 caracteres."
            }), 400

        campos["contrasena"] = contrasena

    resultado = actualizar_usuario(uid, **campos)

    if not resultado["ok"]:
        return jsonify(resultado), 404

    return jsonify({
        "ok": True,
        "mensaje": "Credenciales actualizadas correctamente."
    })
