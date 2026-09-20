"""
Reexportación de los Enum del dominio para la capa de schemas.

Los Enum viven en app/models/enums.py (única fuente de verdad). Aquí solo se
reexportan para que los schemas y routers puedan importarlos desde
`app.schemas.enums` sin conocer la estructura interna de "models". Si algún día
cambia dónde viven, solo se ajusta este archivo.
"""

from app.models.enums import Genre, Role, WorkType

__all__ = ["Role", "WorkType", "Genre"]
