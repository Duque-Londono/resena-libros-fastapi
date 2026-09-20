"""
Enumeraciones del dominio, en UN SOLO lugar reutilizable.

¿Por qué centralizar los Enum aquí?
- Los usan tanto los modelos (columnas de la base de datos) como los schemas de
  Pydantic (validación de la API). Tener una única fuente evita duplicar listas
  y que se desincronicen.
- En la sustentación, si te piden "añade el género 'aventura'" o "agrega un rol",
  solo se toca ESTE archivo.

Todos heredan de `str, Enum`: así el valor viaja como texto legible ("admin",
"book", "fantasy") en el JSON de la API y en la base de datos, en lugar de un
número opaco.
"""

from enum import Enum


class Role(str, Enum):
    """Roles de usuario y sus permisos.

    Jerarquía de permisos (de menor a mayor):
        USER  <  MODERATOR  <  ADMIN

    - USER:      usuario normal. Gestiona SOLO su propio contenido (sus reseñas
                 y su lista de lectura).
    - MODERATOR: además puede gestionar el catálogo de obras (crear/editar/borrar
                 obras).
    - ADMIN:     superconjunto de MODERATOR. Puede todo lo del moderador y, además,
                 eliminar/editar contenido de CUALQUIER usuario.

    La regla "admin es superconjunto de moderator" se implementará en la Fase 3
    dentro de las dependencias de seguridad (un único lugar), no dispersa por los
    endpoints.
    """

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class WorkType(str, Enum):
    """Tipo de obra del catálogo."""

    BOOK = "book"    # Libro
    MOVIE = "movie"  # Película


class Genre(str, Enum):
    """Géneros/etiquetas válidos para una obra.

    Lista pensada para servir tanto a libros como a películas. Al ser un Enum,
    cualquier valor fuera de esta lista será rechazado automáticamente por la
    validación (devolviendo un error 422), sin escribir comprobaciones a mano.
    """

    FICTION = "fiction"                  # Ficción
    NON_FICTION = "non_fiction"          # No ficción
    FANTASY = "fantasy"                  # Fantasía
    SCIENCE_FICTION = "science_fiction"  # Ciencia ficción
    MYSTERY = "mystery"                  # Misterio
    THRILLER = "thriller"                # Suspenso
    ROMANCE = "romance"                  # Romance
    HORROR = "horror"                    # Terror
    DRAMA = "drama"                      # Drama
    COMEDY = "comedy"                    # Comedia
    DOCUMENTARY = "documentary"          # Documental
    BIOGRAPHY = "biography"              # Biografía
    POETRY = "poetry"                    # Poesía
    OTHER = "other"                      # Otro
