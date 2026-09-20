"""
Configuración compartida de las pruebas (fixtures de pytest).

Estrategia de AISLAMIENTO (que ningún test contamine a otro):
- BD de test SEPARADA de la de desarrollo: SQLite EN MEMORIA (sqlite://), que
  vive solo mientras dura el proceso de pytest y nunca toca resenalibros.db.
- create_all()/drop_all() se usan SOLO aquí (nunca en la app, como acordamos):
  antes de CADA test se crean las tablas y después se destruyen. Así cada test
  arranca con una base vacía y predecible.
- Se activa PRAGMA foreign_keys=ON también en el engine de test; sin esto, SQLite
  ignoraría el ondelete=CASCADE y los tests de borrado en cascada darían falsos
  positivos (pasarían sin comprobar realmente la cascada).

UNA SOLA SESIÓN COMPARTIDA (patrón canónico de FastAPI):
- El test (fixtures como `obra`, `usuario_normal`) y las peticiones del TestClient
  (a través del override de get_db) usan EXACTAMENTE la misma sesión. Si usaran
  sesiones distintas, un objeto creado por una fixture podría quedar "detached"
  tras una petición HTTP y lanzar DetachedInstanceError al leer sus atributos.
- expire_on_commit=False: tras un commit, SQLAlchemy no invalida los objetos ya
  cargados, así `obra`, `user`, etc. siguen usables sin quedar detached.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (importa todos los modelos -> los registra en metadata)
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Genre, Role, WorkType
from app.models.work import Work
from app.schemas.user import UserCreate

# --- Engine de test: SQLite en memoria, compartido por todas las conexiones ---
# StaticPool + check_same_thread=False hace que todas las conexiones usen la MISMA
# base en memoria; si no, cada conexión abriría una BD vacía distinta.
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Igual que en producción: activar claves foráneas en cada conexión SQLite.
@event.listens_for(engine_test, "connect")
def _activar_fk_test(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# expire_on_commit=False: clave para que los objetos de las fixtures sigan usables
# (no se "expiran" ni quedan detached) después de que un endpoint haga commit.
TestingSessionLocal = sessionmaker(
    bind=engine_test,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


@pytest.fixture()
def db_session() -> Session:
    """Crea las tablas, entrega UNA sesión y al final la cierra y borra las tablas.

    Esta única sesión es la que compartirán tanto las fixtures como el TestClient
    (ver la fixture `client`), garantizando que ambos vean los mismos datos y los
    mismos objetos vivos.
    """
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """TestClient cuyo get_db devuelve la MISMA sesión que usan las fixtures.

    El override NO cierra la sesión (de eso se encarga la fixture db_session al
    terminar el test); solo la reutiliza para cada petición.
    """

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    # Limpiar el override para no afectar a otros tests/usos de la app.
    app.dependency_overrides.clear()


# --- Fixtures de usuarios y sus cabeceras de autenticación -----------------

def _crear_usuario_con_headers(db: Session, email: str, username: str, role: Role) -> dict:
    """Crea un usuario con el rol dado y prepara su cabecera Authorization.

    Devuelve un dict con el propio usuario y los headers listos para pasar al
    cliente: {"user": User, "headers": {"Authorization": "Bearer <token>"}}.
    El token se genera directamente (no vía /login) para no acoplar estas
    fixtures al endpoint de login.
    """
    user = crud_user.create_user(
        db,
        UserCreate(email=email, username=username, password="password123"),
        role=role,
    )
    token = create_access_token(subject=user.id)
    return {"user": user, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture()
def usuario_normal(db_session: Session) -> dict:
    """Usuario con rol USER, ya creado, con sus headers."""
    return _crear_usuario_con_headers(db_session, "user@test.com", "usuario", Role.USER)


@pytest.fixture()
def admin(db_session: Session) -> dict:
    """Usuario con rol ADMIN, ya creado, con sus headers."""
    return _crear_usuario_con_headers(db_session, "admin@test.com", "admin", Role.ADMIN)


@pytest.fixture()
def moderator(db_session: Session) -> dict:
    """Usuario con rol MODERATOR, ya creado, con sus headers."""
    return _crear_usuario_con_headers(db_session, "mod@test.com", "moderador", Role.MODERATOR)


@pytest.fixture()
def obra(db_session: Session) -> Work:
    """Una obra de ejemplo ya creada en la BD de test."""
    work = Work(
        title="Obra de prueba",
        type=WorkType.BOOK,
        genre=Genre.FICTION,
        description="Una obra para las pruebas.",
        release_year=2020,
    )
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)
    return work
