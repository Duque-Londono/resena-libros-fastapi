"""
Tabla asociativa `reading_list` (lista de lectura / favoritos).

Representa la relación muchos-a-muchos entre usuarios y obras:
un usuario puede tener muchas obras en su lista, y una obra puede estar en las
listas de muchos usuarios.

¿Por qué una Table de SQLAlchemy Core y no un modelo (clase) completo?
- Porque es una tabla "puente" sencilla: solo enlaza user_id con work_id y
  guarda cuándo se añadió. No necesita lógica propia. La forma idiomática en
  SQLAlchemy para esto es una `Table`, que luego se enlaza con `secondary=...`
  en las relaciones de User y Work.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Table

from app.db.base import Base

# Nota: se define con `Column` (estilo Core) porque es una tabla puente, no una
# clase mapeada. La clave primaria es COMPUESTA (user_id + work_id): así un mismo
# usuario no puede añadir dos veces la misma obra a su lista.
reading_list = Table(
    "reading_list",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "work_id",
        ForeignKey("works.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    # Fecha en que la obra se añadió a la lista. Se usa UTC para no depender de
    # la zona horaria del servidor.
    Column(
        "added_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
)
