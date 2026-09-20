"""
Dependencias de seguridad reutilizables para los endpoints.

Aquí vive TODA la lógica de "quién puede hacer qué":
- get_current_user: valida el JWT y devuelve el usuario autenticado.
- La jerarquía de roles (user < moderator < admin) se define UNA sola vez en el
  mapa NIVEL_ROL. Las dependencias require_moderator / require_admin se derivan
  de ese mapa con la fábrica require_min_role, de modo que NO hay comprobaciones
  de rol dispersas por los routers.

En la sustentación, si piden "que los moderadores también puedan X" o "cambia el
nivel necesario", el único sitio a tocar es este archivo.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.crud import user as crud_user
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User

# Le dice a FastAPI de dónde se obtiene el token (endpoint de login). Además hace
# que Swagger muestre el botón "Authorize" para probar endpoints protegidos.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- Jerarquía de roles, en UN SOLO lugar ---------------------------------
# A mayor número, más privilegios. admin es superconjunto de moderator, y este
# de user. Cualquier comprobación de permisos compara estos niveles.
NIVEL_ROL: dict[Role, int] = {
    Role.USER: 1,
    Role.MODERATOR: 2,
    Role.ADMIN: 3,
}


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Obtiene el usuario autenticado a partir del JWT.

    Pasos: decodifica el token -> saca el id del claim "sub" -> busca al usuario.
    Cualquier fallo (token inválido, caducado, usuario inexistente o inactivo)
    responde 401 con la cabecera estándar WWW-Authenticate.
    """
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credenciales_invalidas
        user_id = int(sub)
    except (jwt.PyJWTError, ValueError):
        # PyJWTError cubre firma inválida y token caducado; ValueError, un sub no numérico.
        raise credenciales_invalidas

    user = crud_user.get_by_id(db, user_id)
    if user is None:
        raise credenciales_invalidas
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return user


# Alias de tipo para no repetir la anotación larga en cada endpoint protegido.
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_min_role(rol_minimo: Role):
    """Fábrica de dependencias: exige un rol MÍNIMO según la jerarquía NIVEL_ROL.

    Devuelve una dependencia que primero exige estar autenticado (reutiliza
    get_current_user) y luego comprueba que el nivel del usuario alcance el
    requerido. Al derivar todo de NIVEL_ROL, la regla vive en un único sitio.
    """

    def comprobador(current_user: CurrentUser) -> User:
        if NIVEL_ROL[current_user.role] < NIVEL_ROL[rol_minimo]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol '{rol_minimo.value}' o superior",
            )
        return current_user

    return comprobador


# Dependencias listas para usar en los routers de fases siguientes:
#   def endpoint(user: User = Depends(require_moderator)): ...
require_moderator = require_min_role(Role.MODERATOR)  # moderador o admin
require_admin = require_min_role(Role.ADMIN)          # solo admin
