import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.getenv("FLASK_DEBUG") == "1"


def _secret_key():
    clave = os.getenv("SECRET_KEY")
    if clave:
        return clave
    if not DEBUG:
        raise RuntimeError("SECRET_KEY es obligatoria fuera de modo desarrollo.")
    return "solo-desarrollo"


class Config:
    SECRET_KEY = _secret_key()
    UPLOAD_FOLDER = os.path.abspath(
        os.getenv("PQR_UPLOAD_DIR", str(BASE_DIR / "Base_Datos" / "Evidencias"))
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024
    # Se renueva en cada petición (comportamiento por defecto de Flask): es
    # inactividad, no tiempo fijo desde el login. Corto a propósito porque el
    # sistema se usa en dispositivos compartidos (tablet/PC de la tienda).
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0" if DEBUG else "1") == "1"
    TRUST_PROXY = os.getenv("TRUST_PROXY") == "1"
