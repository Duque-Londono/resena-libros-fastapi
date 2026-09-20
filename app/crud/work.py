"""
CRUD de obras: todas las consultas a la tabla `works` viven aquí.

El router queda fino: solo traduce a HTTP (404, 201, 204). Aquí está la lógica de
datos, reutilizable y fácil de probar sin levantar la API.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import Genre, WorkType
from app.models.work import Work
from app.schemas.work import WorkCreate, WorkUpdate


def get_by_id(db: Session, work_id: int) -> Work | None:
    """Busca una obra por su id. Devuelve None si no existe."""
    return db.get(Work, work_id)


def get_list(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    type: WorkType | None = None,
    genre: Genre | None = None,
) -> list[Work]:
    """Lista obras con paginación y filtros OPCIONALES por tipo y género.

    - skip/limit: paginación (saltar N, devolver como máximo M).
    - type/genre: si vienen, se añaden como condiciones WHERE; si son None, no
      filtran. Así un mismo método sirve para "todo el catálogo" o "solo
      películas de terror" sin duplicar consultas.
    """
    consulta = select(Work)
    if type is not None:
        consulta = consulta.where(Work.type == type)
    if genre is not None:
        consulta = consulta.where(Work.genre == genre)
    # Orden estable por id para que la paginación sea consistente entre llamadas.
    consulta = consulta.order_by(Work.id).offset(skip).limit(limit)
    return list(db.scalars(consulta))


def create(db: Session, work_in: WorkCreate) -> Work:
    """Crea y guarda una obra nueva a partir del schema validado."""
    # model_dump() convierte el schema en un dict con los campos ya validados.
    work = Work(**work_in.model_dump())
    db.add(work)
    db.commit()
    db.refresh(work)  # recarga id y created_at generados por la BD
    return work


def update(db: Session, work: Work, work_in: WorkUpdate) -> Work:
    """Actualiza una obra existente con los campos ENVIADOS (parcial).

    exclude_unset=True hace que solo se toquen los campos que el cliente incluyó
    en la petición; los omitidos conservan su valor. Así el mismo endpoint sirve
    para actualizaciones totales o parciales sin borrar datos por descuido.
    """
    cambios = work_in.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(work, campo, valor)
    db.commit()
    db.refresh(work)
    return work


def delete(db: Session, work: Work) -> None:
    """Elimina una obra. Sus reseñas y entradas de lista caen en cascada."""
    db.delete(work)
    db.commit()
