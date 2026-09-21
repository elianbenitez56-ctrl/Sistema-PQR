import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
TELEFONO_RE = re.compile(r"^[0-9\s\-().+]+$")


def validar_correo(correo):
    return EMAIL_RE.match(correo) is not None


def validar_telefono(telefono):
    return TELEFONO_RE.match(telefono) is not None
