"""
Router de reseñas. Es la fase central: aquí viven las reglas de propiedad.

Rutas:
- GET    /works/{work_id}/reviews  -> público, paginado. 404 si la obra no existe.
- POST   /works/{work_id}/reviews  -> autenticado. 201. 409 si ya reseñó la obra.
- GET    /reviews/{review_id}      -> público. 404 si no existe.
- PUT    /reviews/{review_id}      -> autenticado. Solo dueño o admin (si no, 403).
- DELETE /reviews/{review_id}      -> autenticado. Solo dueño o admin. 204.

Sobre los roles: un MODERATOR NO tiene poder especial sobre reseñas ajenas (su
poder extra es sobre el catálogo de obras). Sobre reseñas, el único que puede
tocar contenido de otros es el ADMIN. Por eso el helper compara con Role.ADMIN,
no con require_moderator.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.crud import review as crud_review
from app.crud import work as crud_work
from app.db.session import get_db
from app.models.enums import Role
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

# Sin prefix porque las rutas cuelgan de dos raíces distintas (/works/... y /reviews/...).
router = APIRouter(tags=["reseñas"])


# --- Helpers de 404 (mensajes uniformes) -----------------------------------

def obtener_resena_o_404(review_id: int, db: Session) -> Review:
    """Devuelve la reseña o lanza 404. Reutilizado por GET/PUT/DELETE."""
    review = crud_review.get_by_id(db, review_id)
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reseña no encontrada")
    return review


def _verificar_obra_existe(work_id: int, db: Session) -> None:
    """Lanza 404 si la obra no existe (para las rutas anidadas en /works)."""
    if crud_work.get_by_id(db, work_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")


# --- REGLA DE PROPIEDAD, en UN SOLO lugar ----------------------------------

def verificar_dueno_o_admin(review: Review, current_user: User) -> None:
    """Permite la acción solo si el usuario es el AUTOR de la reseña o es ADMIN.

    En cualquier otro caso lanza 403. PUT y DELETE usan EXACTAMENTE este mismo
    helper, así la regla de propiedad no se duplica ni se puede desincronizar.

    Nota: se compara con Role.ADMIN a propósito; un moderador no puede editar ni
    borrar reseñas de otros.
    """
    es_dueno = review.user_id == current_user.id
    es_admin = current_user.role == Role.ADMIN
    if not (es_dueno or es_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el autor de la reseña o un administrador pueden hacer esto",
        )


# --- Endpoints -------------------------------------------------------------

@router.get(
    "/works/{work_id}/reviews",
    response_model=list[ReviewRead],
    tags=["reseñas"],
    summary="Listar reseñas de una obra (público, paginado)",
)
def list_reviews_de_obra(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Review]:
    """Devuelve las reseñas de una obra; 404 si la obra no existe."""
    _verificar_obra_existe(work_id, db)
    return crud_review.get_list_by_work(db, work_id, skip=skip, limit=limit)


@router.post(
    "/works/{work_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una reseña para una obra (autenticado)",
)
def create_review(
    work_id: int,
    review_in: ReviewCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Review:
    """Crea una reseña del usuario autenticado sobre la obra indicada.

    - El autor es el usuario del token (no viaja en el body: no se puede suplantar).
    - 404 si la obra no existe.
    - 409 si el usuario ya reseñó esa obra (regla "una reseña por usuario y obra").
    """
    _verificar_obra_existe(work_id, db)
    try:
        return crud_review.create(db, user_id=current_user.id, work_id=work_id, review_in=review_in)
    except crud_review.ResenaDuplicadaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya has publicado una reseña para esta obra",
        )


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewRead,
    summary="Ver una reseña por id (público)",
)
def get_review(
    review_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Review:
    """Devuelve una reseña concreta; 404 si no existe."""
    return obtener_resena_o_404(review_id, db)


@router.put(
    "/reviews/{review_id}",
    response_model=ReviewRead,
    summary="Editar una reseña (solo dueño o admin)",
)
def update_review(
    review_id: int,
    review_in: ReviewUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> Review:
    """Edita una reseña; 404 si no existe, 403 si no eres el autor ni admin."""
    review = obtener_resena_o_404(review_id, db)
    verificar_dueno_o_admin(review, current_user)  # misma regla que DELETE
    return crud_review.update(db, review, review_in)


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una reseña (solo dueño o admin)",
)
def delete_review(
    review_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Elimina una reseña; 404 si no existe, 403 si no eres el autor ni admin."""
    review = obtener_resena_o_404(review_id, db)
    verificar_dueno_o_admin(review, current_user)  # misma regla que PUT
    crud_review.delete(db, review)
