"""
Datos de demostración (seed) para la sustentación.

Crea, si no existen ya:
- 1 administrador.
- 1 usuario normal.
- ~5 obras de ejemplo (libros y películas).

Es IDEMPOTENTE: se puede ejecutar varias veces sin duplicar datos, porque antes
de crear cada registro comprueba si ya existe (por email o por título).

Uso (con las migraciones ya aplicadas):
    python -m app.db.seed

IMPORTANTE: este script usa las funciones normales (create_user hashea la
contraseña con Argon2), así que los usuarios de demo tienen contraseñas reales y
válidas para iniciar sesión.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.models.enums import Genre, Role, WorkType
from app.models.work import Work
from app.schemas.user import UserCreate

# --- Credenciales de demo (visibles a propósito: es un entorno académico) ---
ADMIN = {"email": "admin@demo.com", "username": "admin", "password": "admin12345"}
USUARIO = {"email": "ana@demo.com", "username": "ana", "password": "ana123456"}

# --- Catálogo de demo ---
OBRAS_DEMO = [
    {"title": "El nombre del viento", "type": WorkType.BOOK, "genre": Genre.FANTASY,
     "description": "Primer libro de la Crónica del Asesino de Reyes.", "release_year": 2007},
    {"title": "Cien años de soledad", "type": WorkType.BOOK, "genre": Genre.FICTION,
     "description": "Obra cumbre del realismo mágico.", "release_year": 1967},
    {"title": "Sapiens", "type": WorkType.BOOK, "genre": Genre.NON_FICTION,
     "description": "Breve historia de la humanidad.", "release_year": 2011},
    {"title": "El Padrino", "type": WorkType.MOVIE, "genre": Genre.DRAMA,
     "description": "La saga de la familia Corleone.", "release_year": 1972},
    {"title": "Interestelar", "type": WorkType.MOVIE, "genre": Genre.SCIENCE_FICTION,
     "description": "Viaje espacial en busca de un nuevo hogar para la humanidad.", "release_year": 2014},
]


def _crear_usuario_si_no_existe(db: Session, datos: dict, role: Role) -> None:
    """Crea un usuario solo si su email no está ya registrado."""
    if crud_user.get_by_email(db, datos["email"]):
        print(f"  - Usuario '{datos['email']}' ya existe, se omite.")
        return
    crud_user.create_user(
        db,
        UserCreate(email=datos["email"], username=datos["username"], password=datos["password"]),
        role=role,
    )
    print(f"  + Usuario '{datos['email']}' creado (rol: {role.value}).")


def _crear_obra_si_no_existe(db: Session, datos: dict) -> None:
    """Crea una obra solo si no hay ya otra con el mismo título."""
    existe = db.scalar(select(Work).where(Work.title == datos["title"]))
    if existe:
        print(f"  - Obra '{datos['title']}' ya existe, se omite.")
        return
    db.add(Work(**datos))
    db.commit()
    print(f"  + Obra '{datos['title']}' creada.")


def sembrar() -> None:
    """Ejecuta el sembrado completo dentro de una única sesión."""
    db = SessionLocal()
    try:
        print("Sembrando usuarios...")
        _crear_usuario_si_no_existe(db, ADMIN, Role.ADMIN)
        _crear_usuario_si_no_existe(db, USUARIO, Role.USER)

        print("Sembrando obras...")
        for obra in OBRAS_DEMO:
            _crear_obra_si_no_existe(db, obra)

        print("Seed completado.")
    finally:
        db.close()


if __name__ == "__main__":
    sembrar()
