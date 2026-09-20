"""
Entorno de Alembic.

Adaptado para este proyecto para que:
1. La URL de la base de datos salga de la MISMA configuración que usa la app
   (app.core.config.settings.DATABASE_URL), en lugar de duplicarla en alembic.ini.
   Así, cambiar de SQLite a PostgreSQL en el .env también cambia las migraciones.
2. `target_metadata` apunte a Base.metadata (con TODOS los modelos importados),
   para que `--autogenerate` detecte automáticamente las tablas y sus cambios.
3. En SQLite se use `render_as_batch=True`: SQLite no soporta bien ALTER TABLE,
   y el "batch mode" permite que Alembic haga esos cambios recreando la tabla.
   Es imprescindible si se van a modificar columnas en futuras migraciones.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# --- Hacer visible el paquete "app" ---------------------------------------
# env.py se ejecuta desde la carpeta alembic/; añadimos la raíz del proyecto al
# path para poder importar "app.*".
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.base import Base          # noqa: E402
import app.models  # noqa: E402,F401  (importa todos los modelos -> los registra en metadata)

# Objeto de configuración de Alembic (lee alembic.ini).
config = context.config

# Inyectamos la URL real desde nuestra configuración (pisa la de alembic.ini).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configura el logging definido en alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos objetivo: todas las tablas del proyecto. Habilita autogenerate.
target_metadata = Base.metadata

# ¿Estamos usando SQLite? Entonces activamos el modo batch (ver docstring).
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse a la base de datos (modo 'offline')."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica las migraciones conectándose a la base de datos (modo 'online')."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
