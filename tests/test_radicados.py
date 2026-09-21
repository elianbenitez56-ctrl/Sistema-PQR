"""Concurrencia: cada PQR debe recibir un radicado único."""
from concurrent.futures import ThreadPoolExecutor

from app.repos.pqr import crear_pqr, eliminar_pqr
from wsgi import app  # noqa: F401  (crea el esquema)

MARCA = "TEST-CONCURRENCIA"


def _guardar(_):
    datos = {"cliente": MARCA, "nit": "1", "tipoSol": "Queja", "desc": "x", "email": "", "productos": []}
    try:
        crear_pqr(datos)
        return datos["radicado"]
    except Exception as error:
        return error


def test_radicados_unicos_en_concurrencia():
    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(_guardar, range(8)))
    try:
        errores = [r for r in resultados if isinstance(r, Exception)]
        assert not errores, errores
        assert len(set(resultados)) == 8
    finally:
        for r in resultados:
            if isinstance(r, str):
                eliminar_pqr(r)
