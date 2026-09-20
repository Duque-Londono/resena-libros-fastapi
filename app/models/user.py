"""
Modelo User: los usuarios de la aplicación.

Un usuario puede:
- Escribir muchas reseñas (relación 1 a N con Review).
- Tener muchas obras en su lista de lectura (relación N a M con Work, vía la
  tabla puente `reading_list`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Role
from app.models.reading_list import reading_list

# Import solo para anotaciones de tipo (no en tiempo de ejecución), evitando
# importaciones circulares entre User, Work y Review.
if TYPE_CHECKING:
    from app.models.review import Review
    from app.models.work import Work


class User(Base):
    """Tabla `users`."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Datos de identidad. email y username son ÚNICOS e indexados: se buscan al
    # iniciar sesión, así que el índice acelera esa consulta y `unique` impide
    # duplicados a nivel de base de datos.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    # Aquí se guarda el HASH de la contraseña (Argon2), NUNCA la contraseña en
    # texto plano. El hasheo se implementará en la Fase 3 (core/security.py).
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Rol del usuario. Se almacena como texto ("user"/"moderator"/"admin") gracias
    # al Enum centralizado. Por defecto, todo usuario nuevo es USER.
    # values_callable fuerza a guardar el VALOR del Enum ("user"/"moderator"/
    # "admin") y no su NOMBRE ("USER"/...). Así la BD guarda minúsculas legibles,
    # coincide con lo que viaja en el JSON de la API y facilita el paso a
    # PostgreSQL (que crea un tipo ENUM nativo con esos valores).
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, name="role_enum", values_callable=lambda c: [x.value for x in c]),
        default=Role.USER,
        nullable=False,
    )

    # Permite "desactivar" un usuario sin borrarlo (soft-disable).
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relaciones ---
    # Reseñas escritas por este usuario. cascade="all, delete-orphan": si se borra
    # el usuario, se borran también sus reseñas (no deben quedar huérfanas).
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Obras en la lista de lectura de este usuario (N a M vía `reading_list`).
    reading_list: Mapped[list["Work"]] = relationship(
        secondary=reading_list,
        back_populates="in_reading_lists",
    )
