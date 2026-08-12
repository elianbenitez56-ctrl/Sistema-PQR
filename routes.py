from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import os
import re
from werkzeug.utils import secure_filename

from excel_db import (
    guardar_pqr,
    consultar_pqr,
    guardar_investigacion,
    actualizar_estado_pqr,
    guardar_historial,
    obtener_dashboard,
    guardar_adjunto,
    generar_radicado,
    listar_pqrs,
    eliminar_pqr,
    correo_confirmacion_enviado,
    marcar_correo_confirmacion
)

from email_service import enviar_confirmacion_pqr

from users_db import (
    autenticar_usuario,
    crear_usuario,
    listar_usuarios,
    obtener_usuario_por_id,
    usuario_disponible,
    documento_disponible,
    correo_disponible,
    actualizar_usuario,
    desactivar_usuario,
    eliminar_usuario
)

routes = Blueprint("routes", __name__)


# ==========================================================
# ROLES Y PERMISOS
# ==========================================================

ADMIN = "ADMIN"
VENDEDOR = "VENDEDOR"
LIDER_CALIDAD = "LIDER_CALIDAD"
LIDER_COMERCIAL = "LIDER_COMERCIAL"

# Roles que pueden ver todas las PQR
ROLES_VER_TODO = (ADMIN, LIDER_CALIDAD, LIDER_COMERCIAL)

# Roles que gestionan investigación y estados
ROLES_INVESTIGACION = (ADMIN, LIDER_CALIDAD)


def _usuario_para_sesion(usuario):
    """Expone los datos necesarios para el formulario sin confiar en el navegador."""

    rol = str(usuario.get("rol", "") or "").strip().upper()

    return {
        "id": usuario.get("id"),
        "usuario": usuario.get("usuario", ""),
        "nombre": usuario.get("nombre", ""),
        "rol": usuario.get("rol", ""),
        "linea_producto": usuario.get("linea_producto", ""),
        "empresa": usuario.get("empresa", "INAPEL"),
        "documento": usuario.get("documento", ""),
        "correo": usuario.get("correo", ""),
        "telefono": usuario.get("telefono", ""),
        # El cargo se deriva del rol almacenado; no se fija en el frontend.
        "cargo": rol if rol == VENDEDOR else "",
        # TOROFIL permanece como línea de producto, no como empresa.
        "area": usuario.get("linea_producto", "") or ""
    }


def rol_requerido(*roles):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not session.get("usuario_id"):
                return jsonify({
                    "ok": False,
                    "mensaje": "Debe iniciar sesión para continuar."
                }), 401
            if roles and session.get("rol") not in roles:
                return jsonify({
                    "ok": False,
                    "mensaje": "No tiene permisos para realizar esta acción."
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorador


def sesion_requerida(f):
    return rol_requerido()(f)


# ==========================================================
# AUTENTICACIÓN
# ==========================================================

@routes.route("/api/login", methods=["POST"])
def api_login():

    datos = request.get_json() or {}

    usuario = str(datos.get("usuario", "")).strip()
    contrasena = str(datos.get("contrasena", ""))

    if not usuario or not contrasena:
        return jsonify({
            "ok": False,
            "mensaje": "Ingrese usuario y contraseña."
        }), 400

    resultado = autenticar_usuario(usuario, contrasena)

    if "error" in resultado:
        return jsonify({
            "ok": False,
            "mensaje": resultado["error"]
        }), 401

    session.clear()
    session.permanent = True
    session["usuario_id"] = resultado["id"]
    session["usuario"] = resultado["usuario"]
    session["nombre"] = resultado["nombre"]
    session["rol"] = resultado["rol"]
    session["linea_producto"] = resultado["linea_producto"]
    session["empresa"] = resultado["empresa"]

    return jsonify({
        "ok": True,
        "usuario": _usuario_para_sesion(resultado)
    })


@routes.route("/api/logout", methods=["POST"])
def api_logout():

    session.clear()

    return jsonify({"ok": True})


@routes.route("/api/sesion", methods=["GET"])
def api_sesion():

    if not session.get("usuario_id"):
        return jsonify({"ok": False}), 401

    usuario_actual = obtener_usuario_por_id(session["usuario_id"])

    if not usuario_actual or not usuario_actual.get("activo", True):
        session.clear()
        return jsonify({"ok": False}), 401

    return jsonify({
        "ok": True,
        "usuario": _usuario_para_sesion(usuario_actual)
    })


# ==========================================================
# VALIDACIONES COMUNES
# ==========================================================

EMAIL_REGEX = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
TELEFONO_REGEX = r"^[0-9\s\-().+]+$"


def _validar_correo(correo):
    return re.match(EMAIL_REGEX, correo) is not None


def _validar_telefono(telefono):
    return re.match(TELEFONO_REGEX, telefono) is not None


# ==========================================================
# ADMINISTRACIÓN DE USUARIOS
# ADMIN: gestión completa. LIDER_CALIDAD: solo credenciales.
# ==========================================================

@routes.route("/api/usuarios", methods=["GET"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_listar():

    return jsonify({
        "ok": True,
        "usuarios": listar_usuarios()
    })


@routes.route("/api/usuarios", methods=["POST"])
@rol_requerido(ADMIN, LIDER_CALIDAD)
def api_usuarios_crear():

    datos = request.get_json() or {}

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

    if rol not in (ADMIN, VENDEDOR, LIDER_CALIDAD, LIDER_COMERCIAL):
        return jsonify({
            "ok": False,
            "mensaje": "Rol inválido. Use VENDEDOR, LIDER_CALIDAD o LIDER_COMERCIAL."
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
        if not _validar_correo(correo):
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
        if not _validar_telefono(telefono):
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


@routes.route("/api/usuarios/<int:uid>", methods=["PUT"])
@rol_requerido(ADMIN)
def api_usuarios_actualizar(uid):

    datos = request.get_json() or {}

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
        if rol not in (ADMIN, VENDEDOR, LIDER_CALIDAD, LIDER_COMERCIAL):
            return jsonify({
                "ok": False,
                "mensaje": "Rol inválido. Use VENDEDOR, LIDER_CALIDAD o LIDER_COMERCIAL."
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
        if correo and not _validar_correo(correo):
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
            if not _validar_telefono(telefono):
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


@routes.route("/api/usuarios/<int:uid>", methods=["DELETE"])
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


@routes.route("/api/usuarios/<int:uid>/credenciales", methods=["PUT"])
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

    datos = request.get_json() or {}

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


# ==========================================================
# GUARDAR PQR
# ==========================================================

@routes.route("/api/pqr", methods=["POST"])
@sesion_requerida
def api_guardar_pqr():

    datos = request.get_json()

    if not datos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron datos."
        }), 400

    productos = datos.get("productos", []) or []
    if not isinstance(productos, list):
        return jsonify({
            "ok": False,
            "mensaje": "La información de productos no es válida."
        }), 400

    for producto in productos:
        if not isinstance(producto, dict):
            continue
        plu = str(producto.get("plu", "") or "").strip()
        if plu and not plu.isdigit():
            return jsonify({
                "ok": False,
                "mensaje": "El PLU solo puede contener números."
            }), 400
        # Se conserva como texto para no perder ceros iniciales.
        producto["plu"] = plu

    usuario_actual = obtener_usuario_por_id(session["usuario_id"])

    if not usuario_actual or not usuario_actual.get("activo", True):
        session.clear()
        return jsonify({
            "ok": False,
            "mensaje": "La sesión del usuario ya no es válida. Inicie sesión nuevamente."
        }), 401

    radicado = generar_radicado()
    datos["radicado"] = radicado

    # Los datos del receptor se toman siempre del usuario autenticado.
    # Los valores enviados por el navegador no pueden alterarlos.
    rol_usuario = str(usuario_actual.get("rol", "") or "").strip().upper()
    datos["usuario_id"] = usuario_actual["id"]
    datos["vendedor"] = usuario_actual.get("nombre", "")
    datos["linea"] = usuario_actual.get("linea_producto", "")
    datos["empresa"] = usuario_actual.get("empresa", "INAPEL")
    datos["documento_receptor"] = usuario_actual.get("documento", "")
    datos["correo_receptor"] = usuario_actual.get("correo", "")
    datos["telefono_receptor"] = usuario_actual.get("telefono", "")
    datos["cargo_receptor"] = rol_usuario if rol_usuario == VENDEDOR else ""
    datos["area_receptor"] = usuario_actual.get("linea_producto", "") or ""

    # 1) SIEMPRE se guarda la PQR primero. El correo nunca bloquea el registro.
    guardar_pqr(datos)

    email_enviado = False
    email_estado = "no_intentado"
    email_mensaje = ""

    correo_cliente = str(datos.get("email", "") or "").strip()

    if not correo_cliente:
        email_estado = "sin_correo"
        email_mensaje = "La PQR no tiene un correo electrónico registrado para enviar la confirmación."

    elif not _validar_correo(correo_cliente):
        email_estado = "correo_invalido"
        email_mensaje = "La PQR se guardó, pero el correo del cliente no es válido y no se envió confirmación."

    elif correo_confirmacion_enviado(radicado):
        # Evita duplicados: la confirmación ya se envió para este radicado.
        email_estado = "ya_enviado"
        email_enviado = True
        email_mensaje = "La confirmación ya había sido enviada para este radicado."

    else:
        try:
            ok, motivo = enviar_confirmacion_pqr(radicado, correo_cliente, datos)
            if ok:
                marcar_correo_confirmacion(radicado, True)
                email_enviado = True
                email_estado = "enviado"
                email_mensaje = "Se envió la confirmación al correo registrado."
            else:
                marcar_correo_confirmacion(radicado, False)
                email_estado = "no_enviado"
                email_mensaje = (
                    "PQR registrada correctamente, pero no fue posible enviar "
                    f"el correo de confirmación ({motivo})."
                )
                print(f"[correo] {email_mensaje}")
        except Exception as e:
            # Red de seguridad: ningún error al enviar puede romper el registro.
            marcar_correo_confirmacion(radicado, False)
            email_estado = "no_enviado"
            email_mensaje = "PQR registrada correctamente, pero no fue posible enviar el correo de confirmación."
            print(f"[correo] Error inesperado al enviar para {radicado}: {e}")

    return jsonify({
        "ok": True,
        "radicado": radicado,
        "mensaje": "PQR guardado correctamente",
        "email_enviado": email_enviado,
        "email_estado": email_estado,
        "email_mensaje": email_mensaje
    })


# ==========================================================
# LISTAR TODOS LOS PQR
# ==========================================================

@routes.route("/api/pqr/todos", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_pqr_todos():

    return jsonify(listar_pqrs())


# ==========================================================
# ELIMINAR PQR
# ==========================================================

@routes.route("/api/pqr/<radicado>", methods=["DELETE"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_eliminar_pqr(radicado):

    resultado = eliminar_pqr(radicado)

    if resultado == "not_found":
        return jsonify({
            "ok": False,
            "mensaje": "El registro ya fue eliminado o no existe."
        }), 404

    if resultado != True:
        return jsonify({
            "ok": False,
            "mensaje": "No fue posible eliminar el registro."
        }), 500

    return jsonify({
        "ok": True,
        "mensaje": "Registro eliminado correctamente."
    })


# ==========================================================
# CONSULTAR PQR
# ==========================================================

@routes.route("/api/consultar/<valor>", methods=["GET"])
@sesion_requerida
def api_consultar(valor):

    pqr = consultar_pqr(valor)

    if not pqr:
        return jsonify({
            "error": "PQR no encontrado"
        }), 404

    # Un vendedor solo puede consultar los PQR que él mismo registró.
    if session.get("rol") == VENDEDOR:
        if str(pqr.get("usuario_id", "")) != str(session.get("usuario_id", "")):
            return jsonify({
                "error": "No tiene permisos para consultar este PQR."
            }), 403

    return jsonify(pqr)


# ==========================================================
# GUARDAR SEGUIMIENTO
# ==========================================================

@routes.route("/api/seguimiento", methods=["POST"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_seguimiento():

    datos = request.get_json()

    guardar_investigacion(datos)

    return jsonify({
        "ok": True
    })


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

@routes.route("/api/cambiar_estado", methods=["POST"])
@rol_requerido(*ROLES_INVESTIGACION)
def api_estado():

    datos = request.get_json()

    if not datos or "radicado" not in datos or "estado" not in datos:
        return jsonify({"ok": False, "mensaje": "Faltan datos"}), 400

    actualizar_estado_pqr(
        datos["radicado"],
        datos["estado"]
    )

    guardar_historial(
        datos["radicado"],
        datos["estado"],
        session.get("nombre", "Sistema"),
        "Estado actualizado"
    )

    return jsonify({
        "ok": True
    })


# ==========================================================
# DASHBOARD
# ==========================================================

@routes.route("/api/dashboard", methods=["GET"])
@rol_requerido(*ROLES_VER_TODO)
def api_dashboard():

    return jsonify(obtener_dashboard())

# ==========================================================
# SUBIR EVIDENCIAS
# ==========================================================

@routes.route("/api/evidencias", methods=["POST"])
@sesion_requerida
def api_evidencias():

    radicado = request.form.get("radicado")
    tipo = request.form.get("tipo", "")

    if not radicado:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibió el radicado."
        }), 400

    # Un vendedor solo puede subir evidencias a sus propios PQR.
    if session.get("rol") == VENDEDOR:
        pqr = consultar_pqr(radicado)
        if not pqr or str(pqr.get("usuario_id", "")) != str(session.get("usuario_id", "")):
            return jsonify({
                "ok": False,
                "mensaje": "No tiene permisos para subir evidencias a este PQR."
            }), 403

    archivos = request.files.getlist("archivos")

    if not archivos:
        return jsonify({
            "ok": False,
            "mensaje": "No se recibieron archivos."
        }), 400

    carpeta = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        radicado
    )

    os.makedirs(carpeta, exist_ok=True)

    for archivo in archivos:

        if archivo.filename == "":
            continue

        nombre = secure_filename(archivo.filename)

        ruta = os.path.join(carpeta, nombre)

        archivo.save(ruta)

        guardar_adjunto(
            radicado=radicado,
            tipo=tipo,
            archivo_original=nombre,
            ruta_archivo=ruta,
            observacion="",
            usuario=session.get("nombre", "Cliente")
        )

    return jsonify({
        "ok": True,
        "mensaje": "Evidencias guardadas correctamente."
    })
