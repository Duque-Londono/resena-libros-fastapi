"""
Modelo Review: una reseña con calificación que un usuario hace sobre una obra.

Reglas de negocio importantes que se reflejan aquí, a nivel de base de datos:
- UNA reseña por usuario y obra: restricción única (user_id, work_id). Si se
  intenta crear una segunda, la base de datos la rechaza; en la Fase 3 ese error
  se traducirá a una respuesta HTTP 409 Conflict con un mensaje claro.
- La puntuación (rating) se valida de forma estricta (1..5) con Pydantic en los
  schemas (Fase 3). Aquí, en la tabla, solo definimos el tipo de dato.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.work import Work

# ---------------------------------------------------------------------------
# TIPO DE LA PUNTUACIÓN — AISLADO A PROPÓSITO para poder cambiarlo fácil.
# ---------------------------------------------------------------------------
# Hoy la puntuación es un ENTERO de 1 a 5. Si en la sustentación piden pasarla a
# decimal (p. ej. 4.5), hacen falta DOS cambios EN ESTE ARCHIVO + uno en el schema:
#   1) Cambiar aquí `Integer` por `Float` (en RatingColumnType, abajo).
#   2) Cambiar la anotación de la columna `rating` de `Mapped[int]` a `Mapped[float]`.
#   3) (En otro archivo) cambiar el tipo del campo `rating` en el schema de Pydantic
#      (Fase 3) de int a float y ajustar su validación de rango.
# Además habría que generar una nueva migración de Alembic para alterar la columna.
RatingColumnType = Integer
# ---------------------------------------------------------------------------


class Review(Base):
    """Tabla `reviews`."""

    __tablename__ = "reviews"

    # Restricción única: un usuario no puede reseñar dos veces la misma obra.
    # Es la traducción a la BD de la regla "una reseña por usuario por obra".
    __table_args__ = (
        UniqueConstraint("user_id", "work_id", name="uq_review_user_work"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Claves foráneas. index=True porque se filtran mucho ("reseñas de esta obra",
    # "reseñas de este usuario"). ondelete CASCADE: si se borra el usuario o la
    # obra, sus reseñas se van con ellos.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # Puntuación de 1 a 5 (ver nota sobre RatingColumnType arriba). El rango
    # 1..5 se valida en el schema de Pydantic; la columna solo guarda el número.
    rating: Mapped[int] = mapped_column(RatingColumnType, nullable=False)

    # Texto de la reseña. El límite de caracteres se valida en Pydantic (Fase 3);
    # aquí se refleja con String(2000) como límite físico coherente.
    text: Mapped[str] = mapped_column(String(2000), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Se actualiza automáticamente al editar (onupdate), para saber la última
    # modificación de la reseña.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relaciones ---
    user: Mapped["User"] = relationship(back_populates="reviews")
    work: Mapped["Work"] = relationship(back_populates="reviews")
