"""
Paquete "models": los modelos ORM (tablas) de SQLAlchemy.

Este __init__ importa TODOS los modelos para que, con un solo
`import app.models`, queden registrados en `Base.metadata`.

¿Por qué importa esto? Alembic (y create_all en los tests) necesita "ver" todas
las tablas a través de Base.metadata para generarlas. Si un modelo no se importa
en algún punto, Alembic no lo detecta. Centralizar los imports aquí garantiza
que siempre estén todos registrados.
"""

from app.models.enums import Genre, Role, WorkType
from app.models.reading_list import reading_list
from app.models.review import Review
from app.models.user import User
from app.models.work import Work

# __all__ define qué se exporta con "from app.models import *" y documenta el
# contenido público del paquete.
__all__ = [
    "User",
    "Work",
    "Review",
    "reading_list",
    "Role",
    "WorkType",
    "Genre",
]
