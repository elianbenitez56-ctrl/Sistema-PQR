import re

from app.repos.pqr import HERRAMIENTAS_ANALISIS, normalizar_herramientas
from app.repos.usuarios import listar_usuarios
from app.seguridad import ROLES_COMERCIAL
from app.servicios.catalogo import LINEAS_PRODUCTO, buscar_productos

# ==========================================================
# VALIDACIONES COMUNES
# ==========================================================

EMAIL_REGEX = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
TELEFONO_REGEX = r"^[0-9\s\-().+]+$"


def validar_correo(correo):
    return re.match(EMAIL_REGEX, correo) is not None


def validar_telefono(telefono):
    return re.match(TELEFONO_REGEX, telefono) is not None


def preparar_productos_catalogo(productos):
    """Valida y reemplaza los campos de catálogo por sus valores maestros."""

    preparados = []

    for producto in productos:
        if not isinstance(producto, dict):
            preparados.append(producto)
            continue

        producto = dict(producto)
        producto["tipoDoc"] = "Factura de venta"

        linea = str(producto.get("linea", "") or "").strip().upper()
        referencia_siesa = str(producto.get("referencia_siesa", "") or "").strip()

        # Conserva productos de clientes antiguos que no usaban catálogo.
        if not linea and not referencia_siesa:
            preparados.append(producto)
            continue
        if not linea:
            preparados.append(producto)
            continue

        if linea not in LINEAS_PRODUCTO:
            return None, "La línea de producto no es válida."
        if not referencia_siesa:
            return None, "Debe indicar una REFERENCIA SIESA del catálogo."

        coincidencias = buscar_productos(linea, referencia_siesa)
        if not coincidencias:
            return None, "Referencia no encontrada en el catálogo."

        def coincide(catalogo):
            for campo in ("detalle_presentacion", "producto"):
                enviado = str(producto.get(campo, "") or "").strip()  # noqa: B023 (se invoca dentro de la misma iteración)
                maestro = str(catalogo.get(campo, "") or "").strip()
                if enviado != maestro:
                    return False
            unidad_catalogo = str(catalogo.get("unidad", "") or "").strip()
            if unidad_catalogo:
                unidad_enviada = str(producto.get("unidad", "") or "").strip()  # noqa: B023
                if unidad_enviada != unidad_catalogo:
                    return False
            return True

        seleccionado = next((item for item in coincidencias if coincide(item)), None)
        if not seleccionado:
            return None, "Seleccione una coincidencia válida del catálogo."

        producto_normalizado = {
            "linea": seleccionado["linea"],
            "referencia_siesa": seleccionado["referencia_siesa"],
            "detalle_presentacion": seleccionado["detalle_presentacion"],
            "producto": seleccionado["producto"],
            "unidad": seleccionado["unidad"] or str(producto.get("unidad", "") or "").strip()
        }
        for campo in ("lote", "fechaEmp", "cant", "numDoc"):
            producto_normalizado[campo] = producto.get(campo, "")
        producto_normalizado["tipoDoc"] = "Factura de venta"
        preparados.append(producto_normalizado)

    return preparados, None


def campos_faltantes(datos, campos):
    faltantes = []
    for clave, etiqueta in campos:
        valor = datos.get(clave, "")
        if clave == "herramientas":
            if not isinstance(valor, list) or not valor:
                faltantes.append(etiqueta)
        elif not str(valor or "").strip():
            faltantes.append(etiqueta)
    return faltantes


def preparar_herramientas(datos):
    if "herramientas" not in datos and "herr" not in datos:
        return [], None

    valor = datos.get("herramientas", datos.get("herr", []))
    herramientas = normalizar_herramientas(valor)

    if len(herramientas) != len(set(herramientas)):
        return None, "No puede seleccionar la misma herramienta más de una vez."

    invalidas = [h for h in herramientas if h not in HERRAMIENTAS_ANALISIS]
    if invalidas:
        return None, "La herramienta seleccionada no es válida."

    datos["herramientas"] = herramientas
    return herramientas, None


def campos_modificados(datos, actual, campos):
    return [
        etiqueta
        for clave, etiqueta in campos
        if clave in datos
        and str(datos.get(clave, "") or "").strip()
        != str(actual.get(clave, "") or "").strip()
    ]


def correos_comerciales():
    """Obtiene destinatarios activos desde la hoja Usuarios."""

    destinatarios = []
    vistos = set()

    for usuario in listar_usuarios():
        rol = str(usuario.get("rol", "") or "").strip().upper()
        correo = str(usuario.get("correo", "") or "").strip()
        clave = correo.lower()

        if (
            rol in ROLES_COMERCIAL
            and usuario.get("activo", True)
            and correo
            and clave not in vistos
        ):
            destinatarios.append(correo)
            vistos.add(clave)

    return destinatarios
