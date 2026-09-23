import logging
import os
import time
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

Error = psycopg.Error

# -------------------------------------------------------------------------
# Configuración de conexión PostgreSQL (variables de entorno)
# -------------------------------------------------------------------------

PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "")
PG_DATABASE = os.getenv("PGDATABASE", "sistema_pqr")
PG_SSLMODE = os.getenv("PGSSLMODE", "prefer")  # Supabase/Neon exigen "require"


def _conninfo():
    return (
        f"host={PG_HOST} port={PG_PORT} user={PG_USER} password={PG_PASSWORD} "
        f"dbname={PG_DATABASE} sslmode={PG_SSLMODE}"
    )


# -------------------------------------------------------------------------
# Pool de conexiones y context managers
# -------------------------------------------------------------------------

_POOL = None


def _pool():
    global _POOL
    if _POOL is None:
        _POOL = ConnectionPool(
            conninfo=_conninfo(),
            min_size=1,
            max_size=int(os.getenv("PG_POOL_SIZE", "16")),
            open=False,
        )
        _POOL.open(wait=False)
    return _POOL


@contextmanager
def get_db_connection():
    try:
        with _pool().connection() as conn:
            yield conn
    except Error:
        logger.exception("Error de conexión PostgreSQL")
        raise


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            yield cursor
            if commit:
                conn.commit()
            else:
                conn.rollback()


# -------------------------------------------------------------------------
# Esquema de tablas (ejecutar una sola vez al iniciar)
# -------------------------------------------------------------------------

SCHEMA_SQL = [
    # Tabla usuarios
    """CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        usuario VARCHAR(80) UNIQUE NOT NULL,
        contrasena_hash VARCHAR(255) NOT NULL,
        rol VARCHAR(50) NOT NULL,
        linea_producto VARCHAR(50) DEFAULT '',
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        activo SMALLINT DEFAULT 1,
        fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        documento VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        telefono VARCHAR(20) DEFAULT ''
    );""",
    # Tabla PQR
    """CREATE TABLE IF NOT EXISTS pqr (
        radicado VARCHAR(25) PRIMARY KEY,
        fecha TIMESTAMP NOT NULL,
        hora TIME NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        cliente VARCHAR(150) DEFAULT '',
        nit VARCHAR(20) DEFAULT '',
        contacto VARCHAR(150) DEFAULT '',
        telefono VARCHAR(20) DEFAULT '',
        correo VARCHAR(120) DEFAULT '',
        estado VARCHAR(50) DEFAULT 'Recibido',
        prioridad VARCHAR(50) DEFAULT '',
        descripcion TEXT DEFAULT '',
        expectativa TEXT DEFAULT '',
        productos TEXT DEFAULT '[]',
        empresa VARCHAR(100) DEFAULT 'INAPEL',
        vendedor VARCHAR(150) DEFAULT '',
        linea VARCHAR(50) DEFAULT '',
        usuario_id INT DEFAULT 0,
        correo_confirmacion_enviado SMALLINT DEFAULT 0,
        documento_receptor VARCHAR(20) DEFAULT '',
        correo_receptor VARCHAR(120) DEFAULT '',
        telefono_receptor VARCHAR(20) DEFAULT '',
        cargo_receptor VARCHAR(50) DEFAULT '',
        area_receptor VARCHAR(50) DEFAULT '',
        ciudad_recepcion VARCHAR(100) DEFAULT '',
        departamento_recepcion VARCHAR(100) DEFAULT '',
        medio_recepcion VARCHAR(50) DEFAULT '',
        otro_medio_recepcion VARCHAR(100) DEFAULT ''
    );""",
    # Tabla Historial
    """CREATE TABLE IF NOT EXISTS historial (
        id SERIAL PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        estado VARCHAR(50) NOT NULL,
        usuario VARCHAR(150) NOT NULL,
        fecha DATE NOT NULL,
        hora TIME NOT NULL,
        observacion TEXT DEFAULT ''
    );""",
    "CREATE INDEX IF NOT EXISTS idx_historial_radicado ON historial (radicado);",
    # Tabla Investigaciones
    """CREATE TABLE IF NOT EXISTS investigaciones (
        radicado VARCHAR(25) PRIMARY KEY,
        responsable VARCHAR(150) DEFAULT '',
        cargo VARCHAR(100) DEFAULT '',
        herramienta TEXT DEFAULT '',
        causa TEXT DEFAULT '',
        accion TEXT DEFAULT '',
        notificar VARCHAR(10) DEFAULT '',
        fecha_respuesta DATE,
        fecha_cierre DATE,
        cierre VARCHAR(10) DEFAULT 'No',
        respuesta TEXT DEFAULT '',
        departamentos TEXT DEFAULT '',
        calidad_estado VARCHAR(50) DEFAULT 'pendiente',
        comercial_estado VARCHAR(50) DEFAULT 'pendiente',
        notificacion_comercial_enviada SMALLINT DEFAULT 0,
        respuesta_calidad TEXT DEFAULT '',
        respuesta_comercial TEXT DEFAULT ''
    );""",
    # Tabla Adjuntos
    """CREATE TABLE IF NOT EXISTS adjuntos (
        id SERIAL PRIMARY KEY,
        radicado VARCHAR(25) NOT NULL,
        tipo VARCHAR(50) DEFAULT '',
        archivo_original VARCHAR(255) NOT NULL,
        ruta_archivo VARCHAR(500) NOT NULL,
        fecha DATE,
        hora TIME,
        usuario VARCHAR(150) DEFAULT '',
        observacion TEXT DEFAULT ''
    );""",
    "CREATE INDEX IF NOT EXISTS idx_adjuntos_radicado ON adjuntos (radicado);",
]


# -------------------------------------------------------------------------
# Inicializar tablas al importar
# -------------------------------------------------------------------------

def asegurar_tablas(intentos=30, espera=2):
    """Crea las tablas; espera a que PostgreSQL acepte conexiones (arranque en docker)."""
    for intento in range(1, intentos + 1):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            break
        except Error:
            if intento == intentos:
                raise
            logger.warning("PostgreSQL no disponible (%s/%s), reintentando...", intento, intentos)
            time.sleep(espera)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for sql in SCHEMA_SQL:
                cursor.execute(sql)
        conn.commit()
    logger.info("Tablas PostgreSQL aseguradas correctamente.")
