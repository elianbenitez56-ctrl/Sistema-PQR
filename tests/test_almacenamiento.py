"""Sin Supabase configurado, guardar/borrar deben funcionar contra el disco local."""
import os

from app.config import Config
from app.servicios import almacenamiento


def test_guardar_y_borrar_en_disco_local(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    assert almacenamiento.supabase_configurado() is False

    clave = "PQR-TEST-0001/archivo.txt"
    almacenamiento.guardar(clave, b"contenido de prueba", "text/plain")

    ruta = os.path.join(Config.UPLOAD_FOLDER, clave)
    assert os.path.isfile(ruta)
    assert open(ruta, "rb").read() == b"contenido de prueba"

    assert almacenamiento.url_descarga(clave) is None  # sin Supabase no hay URL firmada

    almacenamiento.borrar([clave])
    assert not os.path.isfile(ruta)

    almacenamiento.borrar_carpeta_local("PQR-TEST-0001")
    assert not os.path.isdir(os.path.join(Config.UPLOAD_FOLDER, "PQR-TEST-0001"))
