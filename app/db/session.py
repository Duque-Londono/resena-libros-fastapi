"""
Motor de base de datos y gestión de sesiones.

Aquí se crea:
- `engine`: la conexión física a la base de datos (definida por DATABASE_URL).
- `SessionLocal`: fábrica de sesiones (cada petición usa una sesión propia).
- `get_db()`: dependencia de FastAPI que abre una sesión, la entrega al endpoint
  y la cierra al terminar (incluso si hubo error). Así nunca quedan sesiones
  colgadas ni conexiones sin liberar.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite necesita un argumento especial cuando se usa con FastAPI, porque por
# defecto solo permite usar la conexión desde el hilo que la creó, y el servidor
# atiende varias peticiones. Con PostgreSQL este argumento no hace falta, por eso
# se añade condicionalmente y así el mismo código sirve para ambas bases.
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

# El "motor" mantiene el pool de conexiones a la base de datos.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    echo=settings.DEBUG,  # En modo DEBUG imprime el SQL generado (útil para aprender/depurar).
)


# SQLite NO respeta las claves foráneas (ni el ondelete=CASCADE) a menos que se
# active explícitamente con "PRAGMA foreign_keys=ON" en CADA conexión. Este
# listener lo ejecuta automáticamente al abrir cada conexión, para que borrar un
# usuario/obra arrastre en cascada sus reseñas y entradas de lista de lectura,
# igual que haría PostgreSQL de fábrica. Solo aplica a SQLite.
if settings.DATABASE_URL.startswith("sqlite"):

    @event.listens_for(Engine, "connect")
    def _activar_foreign_keys_sqlite(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Fábrica de sesiones. autoflush/autocommit en False: controlamos nosotros
# explícitamente cuándo se confirma (commit) o descarta (rollback) una transacción.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una sesión de BD por petición.

    Uso en un endpoint (a partir de la Fase 3):
        def endpoint(db: Session = Depends(get_db)): ...

    El patrón `yield` + `finally` garantiza que la sesión SIEMPRE se cierre,
    aunque el endpoint lance una excepción.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
