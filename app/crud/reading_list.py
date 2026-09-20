"""
CRUD de la lista de lectura / favoritos.

Trabaja sobre la tabla puente `reading_list` (PK compuesta user_id + work_id).
Se usa SQLAlchemy Core (insert/delete/select sobre la Table) en vez de manipular
la relación del ORM, porque es una tabla puente sencilla: así no hay que cargar
en memoria toda la lista del usuario para añadir o quitar un elemento.

Decisión sobre AÑADIR: es IDEMPOTENTE. Si la obra ya está en la lista, no falla
ni duplica (no tiene sentido "añadir dos veces a favoritos"); el router responde
200 en ese caso y 201 cuando realmente se añadió. La PK compuesta impide el
duplicado a nivel de BD de todos modos.
"""

from sqlalchemy import delete as sql_delete, insert, select
from sqlalchemy.orm import Session

from app.models.reading_list import reading_list
from app.models.work import Work


def get_list(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> list[Work]:
    """Devuelve las obras de la lista del usuario, más recientes primero.

    Se une (join) la tabla puente con `works` para traer las obras completas, y
    se ordena por `added_at` descendente (lo último añadido aparece arriba).
    """
    consulta = (
        select(Work)
        .join(reading_list, reading_list.c.work_id == Work.id)
        .where(reading_list.c.user_id == user_id)
        .order_by(reading_list.c.added_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(consulta))


def esta_en_lista(db: Session, user_id: int, work_id: int) -> bool:
    """Indica si una obra ya está en la lista del usuario."""
    consulta = select(reading_list.c.work_id).where(
        reading_list.c.user_id == user_id,
        reading_list.c.work_id == work_id,
    )
    return db.scalar(consulta) is not None


def add(db: Session, user_id: int, work_id: int) -> bool:
    """Añade una obra a la lista del usuario (idempotente).

    NO comprueba que la obra exista; eso lo hace el router (que sabe dar 404).
    Devuelve True si se añadió, False si ya estaba (para que el router elija el
    código de estado: 201 nuevo vs 200 ya existente).
    """
    if esta_en_lista(db, user_id, work_id):
        return False
    db.execute(insert(reading_list).values(user_id=user_id, work_id=work_id))
    db.commit()
    return True


def remove(db: Session, user_id: int, work_id: int) -> bool:
    """Quita una obra de la lista del usuario.

    Devuelve True si se eliminó algo, False si la obra no estaba en la lista
    (para que el router responda 404 en ese caso).
    """
    resultado = db.execute(
        sql_delete(reading_list).where(
            reading_list.c.user_id == user_id,
            reading_list.c.work_id == work_id,
        )
    )
    db.commit()
    # rowcount indica cuántas filas se borraron: 0 = no estaba en la lista.
    return resultado.rowcount > 0
