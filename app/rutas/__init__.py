from app.rutas import (
    catalogo,
    evidencias,
    pqr,
    seguimiento,
    sesion,
    usuarios,
)

blueprints = [m.bp for m in (sesion, usuarios, catalogo, pqr, seguimiento, evidencias)]
