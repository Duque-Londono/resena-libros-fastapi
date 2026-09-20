"""
Router de la lista de lectura / favoritos.

Rutas (todas requieren autenticación):
- GET    /me/reading-list            -> ver MI lista.
- POST   /me/reading-list/{work_id}  -> añadir una obra a MI lista. 404 si no existe.
- DELETE /me/reading-list/{work_id}  -> quitar una obra de MI lista. 404 si no estaba.

CLAVE de seguridad: el usuario SIEMPRE sale del token (current_user.id), NUNCA de
la ruta ni del body. El prefijo "/me" es literal: no hay ningún endpoint que
reciba un id de usuario, así que es imposible ver o tocar la lista de otro.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser
from app.crud import reading_list as crud_reading_list
from app.crud import work as crud_work
from app.db.session import get_db
from app.models.work import Work
from app.schemas.reading_list import ReadingListItem

router = APIRouter(prefix="/me/reading-list", tags=["lista de lectura"])


def _verificar_obra_existe(work_id: int, db: Session) -> None:
    """Lanza 404 si la obra no existe (antes de añadirla a la lista)."""
    if crud_work.get_by_id(db, work_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obra no encontrada")


@router.get(
    "",
    response_model=list[ReadingListItem],
    summary="Ver mi lista de lectura (autenticado)",
)
def get_my_reading_list(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Work]:
    """Devuelve las obras de la lista del usuario autenticado."""
    return crud_reading_list.get_list(db, current_user.id, skip=skip, limit=limit)


@router.post(
    "/{work_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Añadir una obra a mi lista (autenticado, idempotente)",
)
def add_to_my_reading_list(
    work_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
) -> dict[str, str]:
    """Añade la obra a la lista del usuario.

    - 404 si la obra no existe.
    - 201 si se añadió; 200 si ya estaba (operación idempotente, no falla).
    """
    _verificar_obra_existe(work_id, db)
    anadida = crud_reading_list.add(db, current_user.id, work_id)
    if not anadida:
        # Ya estaba en la lista: no es un error, pero tampoco se "creó" nada nuevo.
        response.status_code = status.HTTP_200_OK
        return {"detail": "La obra ya estaba en tu lista"}
    return {"detail": "Obra añadida a tu lista"}


@router.delete(
    "/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar una obra de mi lista (autenticado)",
)
def remove_from_my_reading_list(
    work_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Quita la obra de la lista del usuario; 404 si no estaba en ella."""
    eliminada = crud_reading_list.remove(db, current_user.id, work_id)
    if not eliminada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La obra no está en tu lista",
        )
