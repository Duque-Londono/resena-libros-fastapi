"""
Schemas relacionados con el token JWT.
"""

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Respuesta del endpoint de login.

    `token_type` es "bearer" por convención de OAuth2: el cliente debe enviar el
    token en la cabecera  Authorization: Bearer <access_token>.
    """

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    )


class TokenPayload(BaseModel):
    """Contenido esperado dentro del JWT (para validar tras decodificar).

    `sub` es el id del usuario (como texto, según el estándar JWT).
    """

    sub: str | None = None
