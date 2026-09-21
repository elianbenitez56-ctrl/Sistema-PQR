from functools import wraps
from flask import jsonify, session


# ==========================================================
# ROLES Y PERMISOS
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

# Roles que pueden ver todas las PQR
ROLES_VER_TODO = (
    ADMIN,
    LIDER_CALIDAD,
    LIDER_COMERCIAL,
    COORDINADORA_COMERCIAL,
    DIRECTORA_COMERCIAL,
    COMERCIAL,
    DIRECTOR_PRODUCCION
)

# Roles que gestionan investigación y estados
ROLES_INVESTIGACION = (ADMIN, LIDER_CALIDAD)

# Roles que pueden diligenciar la sección de seguimiento comercial.
ROLES_COMERCIAL = (
    LIDER_COMERCIAL,
    COORDINADORA_COMERCIAL,
    DIRECTORA_COMERCIAL,
    COMERCIAL
)

ROLES_SEGUIMIENTO = (ADMIN, LIDER_CALIDAD) + ROLES_COMERCIAL


def rol_requerido(*roles):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not session.get("usuario_id"):
                return jsonify({
                    "ok": False,
                    "mensaje": "Debe iniciar sesión para continuar."
                }), 401
            rol_actual = session.get("rol")
            # ADMIN es el superadministrador: conserva acceso a cualquier ruta protegida.
            if roles and rol_actual != ADMIN and rol_actual not in roles:
                return jsonify({
                    "ok": False,
                    "mensaje": "No tiene permisos para realizar esta acción."
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorador


def sesion_requerida(f):
    return rol_requerido()(f)
