"""
Schemas de usuario: qué datos entran (registro) y qué datos salen (respuesta).

Regla de seguridad clave: el schema de SALIDA (UserRead) NUNCA incluye
`hashed_password`. Aunque el modelo de la base de datos lo tenga, la API jamás lo
expone. Al usar un schema distinto para la salida, es imposible filtrarlo por
descuido.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.enums import Role


class UserBase(BaseModel):
    """Campos comunes de un usuario (compartidos por entrada y salida)."""

    # EmailStr valida automáticamente que tenga formato de correo válido.
    email: EmailStr
    # Límites de longitud del nombre de usuario, validados por Pydantic.
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """Datos que envía el cliente al REGISTRARSE (POST /auth/register).

    La contraseña llega en texto plano SOLO aquí y solo se usa para calcular su
    hash; nunca se almacena tal cual. El límite de 8..128 evita contraseñas
    demasiado débiles o absurdamente largas.
    """

    password: str = Field(min_length=8, max_length=128)

    # Ejemplo que se mostrará en Swagger para que probar el registro sea trivial.
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "ana@ejemplo.com",
                    "username": "ana_reads",
                    "password": "unaClaveSegura123",
                }
            ]
        }
    )


class UserRead(UserBase):
    """Datos que la API DEVUELVE sobre un usuario (sin la contraseña).

    from_attributes=True permite construir este schema directamente desde un
    objeto ORM (User), leyendo sus atributos.
    """

    id: int
    role: Role
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "ana@ejemplo.com",
                    "username": "ana_reads",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2026-09-20T18:00:00Z",
                }
            ]
        },
    )
