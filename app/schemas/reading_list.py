"""
Schema de salida de la lista de lectura.

Decisión: la lista DEVUELVE las obras completas, reutilizando `WorkRead`.
Motivo: es lo más útil para el cliente (ya trae título, tipo, género, etc. sin
tener que pedir cada obra por separado) y evita crear un schema casi idéntico.

Si en el futuro se quisiera exponer también CUÁNDO se añadió cada obra
(`added_at`, que vive en la tabla puente), bastaría con definir aquí un
`ReadingListItem` con los campos de la obra + `added_at` y ajustar
crud/reading_list.get_list para devolver esa información. De momento no se hace
por simplicidad (esta es la fase más simple).
"""

from app.schemas.work import WorkRead

# Alias explícito para que el router y la documentación dejen claro qué se
# devuelve en la lista, sin acoplarse a que "sea" WorkRead.
ReadingListItem = WorkRead

__all__ = ["ReadingListItem"]
