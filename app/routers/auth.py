"""
Router de autenticación: registro, login (emisión de JWT) y perfil propio.

Endpoints:
- POST /auth/register : crea una cuenta nueva (rol USER). 409 si ya existe.
- POST /auth/login    : valida credenciales y devuelve un JWT.
- GET  /auth/me       : devuelve los datos del usuario autenticado.

El router es fino a propósito: la lógica de datos está en crud/user.py, la
criptografía en core/security.py y los permisos en core/dependencies.py.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

# prefix="/auth" antepone esa ruta a todos los endpoints; tags agrupa en Swagger.
router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post(
    "/register",
    response_model=UserRead,           # la salida NUNCA incluye la contraseña
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario nuevo",
)
def register(
    user_in: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """Crea una cuenta con rol USER.

    Rechaza con 409 Conflict si el email o el username ya están en uso, con un
    mensaje claro que indica cuál está repetido.
    """
    if crud_user.get_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )
    if crud_user.get_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso",
        )
    return crud_user.create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión y obtener un token JWT",
)
def login(
    # OAuth2PasswordRequestForm lee un formulario con los campos "username" y
    # "password". Aquí "username" puede ser el email O el nombre de usuario.
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Valida credenciales y devuelve el token de acceso.

    Si son incorrectas responde 401. No se revela si falló el usuario o la
    contraseña, para no dar pistas a un atacante.
    """
    user = crud_user.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Ver mi propio perfil",
)
def read_me(current_user: CurrentUser) -> UserRead:
    """Devuelve los datos del usuario autenticado (requiere token válido)."""
    return current_user
