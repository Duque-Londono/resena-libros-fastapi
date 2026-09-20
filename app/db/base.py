"""
Clase Base declarativa de SQLAlchemy 2.0.

Todos los modelos (User, Work, Review...) heredarán de esta clase `Base`.
Al heredar, SQLAlchemy registra cada modelo en `Base.metadata`, que es el
"mapa" de todas las tablas. Alembic lee ese mapa para saber qué tablas deben
existir y generar las migraciones automáticamente.

¿Por qué un archivo aparte solo para Base?
- Para evitar importaciones circulares: los modelos importan `Base` desde aquí,
  y este archivo NO importa los modelos (así no hay dependencia en círculo).
- El "registro" de los modelos en metadata se hace en app/models/__init__.py,
  que sí los importa a todos.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base común para todos los modelos ORM del proyecto.

    En SQLAlchemy 2.0 se recomienda heredar de DeclarativeBase (estilo moderno,
    con anotaciones de tipo `Mapped[...]`) en lugar del antiguo declarative_base().
    """

    pass
