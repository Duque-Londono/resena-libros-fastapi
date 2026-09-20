"""
Schemas de obra (libro/película): validan la entrada y dan forma a la salida.

Toda la validación de datos de una obra vive AQUÍ (longitudes, rango de año,
Enum de tipo y género). Los routers no repiten estas comprobaciones.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import Genre, WorkType

# El año máximo aceptado se calcula una vez al cargar el módulo: año actual + 5.
# Se permite un pequeño margen a futuro para obras ya anunciadas pero no estrenadas.
# El mínimo (1450) es aproximadamente la invención de la imprenta.
_ANIO_MIN = 1450
_ANIO_MAX = datetime.now().year + 5


class WorkBase(BaseModel):
    """Campos comunes de una obra."""

    title: str = Field(min_length=1, max_length=255)
    type: WorkType
    genre: Genre
    # Opcionales: pueden faltar (None). description es texto libre; el límite alto
    # coincide con la columna Text de la BD.
    description: str | None = Field(default=None, max_length=2000)
    release_year: int | None = Field(default=None, ge=_ANIO_MIN, le=_ANIO_MAX)


class WorkCreate(WorkBase):
    """Datos para CREAR una obra (POST /works). title, type y genre son obligatorios."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Dune",
                    "type": "book",
                    "genre": "science_fiction",
                    "description": "Novela clásica de ciencia ficción de Frank Herbert.",
                    "release_year": 1965,
                }
            ]
        }
    )


class WorkUpdate(BaseModel):
    """Datos para ACTUALIZAR una obra (PUT /works/{id}).

    TODOS los campos son opcionales para permitir actualizaciones parciales: el
    cliente envía solo lo que quiere cambiar. Se repiten aquí las validaciones
    (no hereda de WorkBase) porque los tipos y obligatoriedad son distintos.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    type: WorkType | None = None
    genre: Genre | None = None
    description: str | None = Field(default=None, max_length=2000)
    release_year: int | None = Field(default=None, ge=_ANIO_MIN, le=_ANIO_MAX)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "Edición revisada y ampliada.",
                    "release_year": 1966,
                }
            ]
        }
    )


class WorkRead(WorkBase):
    """Datos que la API DEVUELVE sobre una obra.

    from_attributes=True permite construir el schema directamente desde el objeto
    ORM Work.
    """

    id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "title": "Dune",
                    "type": "book",
                    "genre": "science_fiction",
                    "description": "Novela clásica de ciencia ficción de Frank Herbert.",
                    "release_year": 1965,
                    "created_at": "2026-09-20T18:00:00Z",
                }
            ]
        },
    )
