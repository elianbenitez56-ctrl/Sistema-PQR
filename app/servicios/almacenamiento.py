"""Almacenamiento de evidencias adjuntas a un PQR.

Dos formas, en este orden de preferencia:
  1. Supabase Storage (SUPABASE_URL + SUPABASE_SERVICE_KEY) — necesario en Render, donde
     el disco no persiste entre deploys sin un plan de pago.
  2. Disco local (PQR_UPLOAD_DIR) — sirve en local/Docker con el volumen `evidencias`.

`clave` identifica el archivo de forma única: "<radicado>/<nombre_seguro>".
"""
import json
import logging
import mimetypes
import os
import shutil
import urllib.error
import urllib.request

from app.config import Config

logger = logging.getLogger(__name__)


def _var(nombre, defecto=""):
    return os.environ.get(nombre, defecto)


def supabase_configurado():
    return bool(_var("SUPABASE_URL") and _var("SUPABASE_SERVICE_KEY"))


def _bucket():
    return _var("SUPABASE_BUCKET", "evidencias")


def _base_url():
    return _var("SUPABASE_URL").rstrip("/")


def _headers():
    clave = _var("SUPABASE_SERVICE_KEY")
    return {"Authorization": f"Bearer {clave}", "apikey": clave}


def guardar(clave, datos, tipo_mime=None):
    """Guarda el contenido (bytes) bajo `clave`. Lanza RuntimeError si falla."""
    tipo_mime = tipo_mime or mimetypes.guess_type(clave)[0] or "application/octet-stream"

    if supabase_configurado():
        url = f"{_base_url()}/storage/v1/object/{_bucket()}/{clave}"
        peticion = urllib.request.Request(
            url, data=datos, method="POST",
            headers={**_headers(), "Content-Type": tipo_mime, "x-upsert": "true"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=30):
                return
        except urllib.error.HTTPError as error:
            detalle = error.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Supabase Storage HTTP {error.code}: {detalle}") from error
        except Exception as error:
            raise RuntimeError(f"Error al subir a Supabase Storage: {error}") from error

    ruta = os.path.join(Config.UPLOAD_FOLDER, clave)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(datos)


def url_descarga(clave, segundos=600):
    """URL para descargar el archivo (firmada en Supabase; ruta local en disco)."""
    if not supabase_configurado():
        return None

    url = f"{_base_url()}/storage/v1/object/sign/{_bucket()}/{clave}"
    peticion = urllib.request.Request(
        url, data=f'{{"expiresIn": {int(segundos)}}}'.encode("utf-8"), method="POST",
        headers={**_headers(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15) as respuesta:
            data = json.loads(respuesta.read().decode("utf-8"))
            return f"{_base_url()}/storage/v1{data['signedURL']}"
    except Exception:
        logger.exception("No fue posible firmar la URL de %s", clave)
        return None


def borrar(claves):
    """Borra una lista de claves. No lanza si alguna no existe."""
    claves = [c for c in claves if c]
    if not claves:
        return

    if supabase_configurado():
        url = f"{_base_url()}/storage/v1/object/{_bucket()}"
        peticion = urllib.request.Request(
            url, data=json.dumps({"prefixes": claves}).encode("utf-8"), method="DELETE",
            headers={**_headers(), "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=15):
                pass
        except Exception:
            logger.exception("No fue posible borrar de Supabase Storage: %s", claves)
        return

    for clave in claves:
        ruta = os.path.join(Config.UPLOAD_FOLDER, clave)
        if os.path.isfile(ruta):
            os.remove(ruta)


def borrar_carpeta_local(radicado):
    """Borra la carpeta local del radicado (solo aplica cuando no hay Supabase configurado)."""
    if supabase_configurado():
        return
    carpeta = os.path.join(Config.UPLOAD_FOLDER, radicado)
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)
