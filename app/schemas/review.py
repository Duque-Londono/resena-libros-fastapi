"""
Schemas de reseña: validan la entrada y dan forma a la salida.

Decisión de diseño importante: el body de creación/edición NO incluye user_id ni
work_id. El autor se obtiene del token (nadie puede reseñar "en nombre de otro")
y la obra, de la ruta (/works/{work_id}/reviews). Así se evita la suplantación y
el cliente no puede falsear a quién pertenece la reseña.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Límites de la puntuación y del texto, en constantes reutilizables. TEXTO_MAX
# coincide con la columna String(2000) del modelo Review.
RATING_MIN = 1
RATING_MAX = 5
TEXTO_MAX = 2000


class ReviewCreate(BaseModel):
    """Datos para CREAR una reseña (POST /works/{work_id}/reviews)."""

    # Puntuación entre 1 y 5 (validada por Pydantic). Si se cambia a decimal en el
    # futuro, aquí int -> float, además de los cambios en el modelo (ver review.py).
    rating: int = Field(ge=RATING_MIN, le=RATING_MAX)
    # Texto obligatorio y con longitud limitada (1..2000) para evitar reseñas
    # vacías o desproporcionadas.
    text: str = Field(min_length=1, max_length=TEXTO_MAX)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"rating": 5, "text": "Una obra maestra, me atrapó desde la primera página."}
            ]
        }
    )


class ReviewUpdate(BaseModel):
    """Datos para ACTUALIZAR una reseña (PUT /reviews/{id}).

    Ambos campos son opcionales para permitir edición parcial (cambiar solo la
    nota, o solo el texto).
    """

    rating: int | None = Field(default=None, ge=RATING_MIN, le=RATING_MAX)
    text: str | None = Field(default=None, min_length=1, max_length=TEXTO_MAX)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"rating": 4, "text": "Tras releerla, le bajo un poco la nota pero sigue siendo genial."}
            ]
        }
    )


class ReviewRead(BaseModel):
    """Datos que la API DEVUELVE sobre una reseña.

    Incluye user_id y work_id para que el cliente sepa de quién es y sobre qué
    obra, sin exponer datos sensibles del usuario.
    """

    id: int
    user_id: int
    work_id: int
    rating: int
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "user_id": 2,
                    "work_id": 1,
                    "rating": 5,
                    "text": "Una obra maestra, me atrapó desde la primera página.",
                    "created_at": "2026-09-20T18:00:00Z",
                    "updated_at": "2026-09-20T18:00:00Z",
                }
            ]
        },
    )
