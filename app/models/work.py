"""
Modelo Work: una obra del catálogo (libro o película).

Una obra:
- Recibe muchas reseñas (relación 1 a N con Review).
- Puede estar en la lista de lectura de muchos usuarios (N a M con User, vía la
  tabla puente `reading_list`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Genre, WorkType
from app.models.reading_list import reading_list

if TYPE_CHECKING:
    from app.models.review import Review
    from app.models.user import User


class Work(Base):
    """Tabla `works` (obras: libros y películas)."""

    __tablename__ = "works"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)

    # Tipo (libro/película) y género: ambos validados por Enum centralizado.
    # values_callable => se guarda el VALOR ("book"/"movie", "fantasy"...) y no el
    # NOMBRE ("BOOK"...). Mantiene la BD en minúsculas y facilita PostgreSQL.
    type: Mapped[WorkType] = mapped_column(
        SAEnum(WorkType, name="work_type_enum", values_callable=lambda c: [x.value for x in c]),
        nullable=False,
    )
    genre: Mapped[Genre] = mapped_column(
        SAEnum(Genre, name="genre_enum", values_callable=lambda c: [x.value for x in c]),
        nullable=False,
    )

    # Descripción/sinopsis. Text (no String) porque puede ser largo y sin límite fijo.
    # Es opcional: por eso Mapped[str | None] y nullable=True.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Año de publicación/estreno. Opcional.
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relaciones ---
    # Reseñas de esta obra. Si se borra la obra, se borran sus reseñas.
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="work",
        cascade="all, delete-orphan",
    )

    # Usuarios que tienen esta obra en su lista de lectura (N a M).
    in_reading_lists: Mapped[list["User"]] = relationship(
        secondary=reading_list,
        back_populates="reading_list",
    )
