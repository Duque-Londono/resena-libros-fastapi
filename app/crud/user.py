"""
CRUD de usuarios: todas las consultas a la tabla `users` viven aquí.

Separar esto del router permite:
- Reutilizar (p. ej. el seed usa create_user igual que el registro).
- Probar la lógica de datos sin levantar la API.
- Mantener el router centrado solo en HTTP (códigos de estado, respuestas).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.enums import Role
from app.models.user import User
from app.schemas.user import UserCreate


def get_by_id(db: Session, user_id: int) -> User | None:
    """Busca un usuario por su id (usado al validar el token)."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Busca un usuario por email (para evitar duplicados y para el login)."""
    return db.scalar(select(User).where(User.email == email))


def get_by_username(db: Session, username: str) -> User | None:
    """Busca un usuario por nombre de usuario."""
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, user_in: UserCreate, role: Role = Role.USER) -> User:
    """Crea y guarda un usuario nuevo.

    IMPORTANTE: aquí se calcula el HASH de la contraseña; en la BD nunca entra el
    texto plano. El parámetro `role` permite crear administradores desde el seed
    reutilizando esta misma función (por defecto, un registro normal es USER).

    No comprueba duplicados: esa validación (y el 409) se hace en el router, que
    es quien conoce el contexto HTTP.
    """
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # recarga el objeto con los valores generados por la BD (id, created_at)
    return user


def authenticate(db: Session, identificador: str, password: str) -> User | None:
    """Valida credenciales para el login.

    Acepta que `identificador` sea el email O el username, para que el usuario
    pueda iniciar sesión con cualquiera de los dos (más cómodo en la demo).
    Devuelve el usuario si la contraseña coincide; None en caso contrario.
    """
    user = get_by_email(db, identificador) or get_by_username(db, identificador)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
