"""
Router del catálogo de obras (libros/películas).

Reglas de acceso:
- LECTURA (GET) es pública: cualquiera consulta el catálogo.
- ESCRITURA (POST/PUT/DELETE) requiere rol moderador o superior.

Los permisos se aplican SOLO como dependencia en el decorador
(dependencies=[Depends(require_moderator)]); dentro del cuerpo de los endpoints
NO hay ninguna comprobación de rol. El 404 se centraliza en el helper
`obtener_obra_o_404` para que sea idéntico en todos los endpoints que lo usan.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_moderator
from app.crud import work as crud_work
from app.db.session import get_db
from app.models.enums import Genre, WorkType
from app.models.work import Work
from app.schemas.work import WorkCreate, WorkRead, WorkUpdate

router = APIRouter(prefix="/works", tags=["catálogo de obras"])


def obtener_obra_o_404(work_id: int, db: Session) -> Work:
    """Devuelve la obra o lanza 404 con un mensaje uniforme.

    Se usa en todos los endpoints que operan sobre una obra concreta, para no
    repetir la comprobación ni el mensaje de error.
    """
    work = crud_work.get_by_id(db, work_id)
    if work is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Obra no encontrada",
        )
    return work


@router.get(
    "",
    response_model=list[WorkRead],
    summary="Listar obras (público, con paginación y filtros)",
)
def list_works(
    db: Annotated[Session, Depends(get_db)],
    # Paginación con límites validados por FastAPI (evita pedir páginas gigantes).
    skip: Annotated[int, Query(ge=0, description="Cuántas obras saltar")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Máximo de obras a devolver")] = 20,
    # Filtros opcionales; al ser Enum, Swagger muestra un desplegable y valida solo.
    type: Annotated[WorkType | None, Query(description="Filtrar por tipo")] = None,
    genre: Annotated[Genre | None, Query(description="Filtrar por género")] = None,
) -> list[Work]:
    """Devuelve el catálogo, opcionalmente filtrado y paginado."""
    return crud_work.get_list(db, skip=skip, limit=limit, type=type, genre=genre)


@router.get(
    "/{work_id}",
    response_model=WorkRead,
    summary="Ver una obra por id (público)",
)
def get_work(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> Work:
    """Devuelve una obra concreta; 404 si no existe."""
    return obtener_obra_o_404(work_id, db)


@router.post(
    "",
    response_model=WorkRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_moderator)],  # permiso: moderador o admin
    summary="Crear una obra (moderador/admin)",
)
def create_work(
    work_in: WorkCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Work:
    """Crea una obra nueva en el catálogo."""
    return crud_work.create(db, work_in)


@router.put(
    "/{work_id}",
    response_model=WorkRead,
    dependencies=[Depends(require_moderator)],  # permiso: moderador o admin
    summary="Actualizar una obra (moderador/admin)",
)
def update_work(
    work_id: int,
    work_in: WorkUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Work:
    """Actualiza (total o parcialmente) una obra existente; 404 si no existe."""
    work = obtener_obra_o_404(work_id, db)
    return crud_work.update(db, work, work_in)


@router.delete(
    "/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_moderator)],  # permiso: moderador o admin
    summary="Eliminar una obra (moderador/admin)",
)
def delete_work(
    work_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Elimina una obra existente; 404 si no existe. Devuelve 204 sin cuerpo."""
    work = obtener_obra_o_404(work_id, db)
    crud_work.delete(db, work)
