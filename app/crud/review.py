"""
CRUD de reseñas: todas las consultas a la tabla `reviews` viven aquí.

Punto delicado de esta fase: la regla "una reseña por usuario y obra". Se defiende
en DOS capas:
1. Comprobación previa (existe_reseña) para dar un 409 claro en el caso normal.
2. Captura de IntegrityError de la restricción única `uq_review_user_work` como
   red de seguridad ante una condición de carrera (dos peticiones casi
   simultáneas del mismo usuario sobre la misma obra). Sin esta segunda capa, esa
   carrera provocaría un error 500 en lugar de un 409 limpio.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


class ResenaDuplicadaError(Exception):
    """Se lanza cuando un usuario intenta reseñar dos veces la misma obra.

    Es una excepción propia del dominio: el CRUD no conoce HTTP, así que en vez
    de lanzar un 409 directamente, lanza esto y el router lo traduce a 409. Así
    la capa de datos queda desacoplada de la capa web.
    """


def get_by_id(db: Session, review_id: int) -> Review | None:
    """Busca una reseña por su id. Devuelve None si no existe."""
    return db.get(Review, review_id)


def get_list_by_work(db: Session, work_id: int, skip: int = 0, limit: int = 20) -> list[Review]:
    """Lista las reseñas de una obra concreta, paginadas y ordenadas por id."""
    consulta = (
        select(Review)
        .where(Review.work_id == work_id)
        .order_by(Review.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(consulta))


def existe_resena(db: Session, user_id: int, work_id: int) -> bool:
    """Indica si el usuario ya tiene una reseña para esa obra."""
    consulta = select(Review.id).where(
        Review.user_id == user_id, Review.work_id == work_id
    )
    return db.scalar(consulta) is not None


def create(db: Session, user_id: int, work_id: int, review_in: ReviewCreate) -> Review:
    """Crea una reseña para (user_id, work_id).

    IMPORTANTE: no comprueba que la obra exista; eso lo hace el router (que sabe
    devolver 404). Aquí solo se ocupa de la unicidad usuario-obra.

    - Comprobación previa: si ya existe, lanza ResenaDuplicadaError (-> 409).
    - Red de seguridad: si la restricción única salta igualmente (carrera),
      captura IntegrityError, revierte y lanza también ResenaDuplicadaError.
    """
    if existe_resena(db, user_id, work_id):
        raise ResenaDuplicadaError

    review = Review(
        user_id=user_id,
        work_id=work_id,
        rating=review_in.rating,
        text=review_in.text,
    )
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        # Otra petición insertó la reseña entre nuestra comprobación y el commit.
        db.rollback()
        raise ResenaDuplicadaError
    db.refresh(review)
    return review


def update(db: Session, review: Review, review_in: ReviewUpdate) -> Review:
    """Actualiza una reseña con los campos enviados (parcial).

    exclude_unset=True: solo se tocan los campos incluidos en la petición; los
    omitidos conservan su valor. `updated_at` se actualiza solo (onupdate del modelo).
    """
    cambios = review_in.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(review, campo, valor)
    db.commit()
    db.refresh(review)
    return review


def delete(db: Session, review: Review) -> None:
    """Elimina una reseña."""
    db.delete(review)
    db.commit()
