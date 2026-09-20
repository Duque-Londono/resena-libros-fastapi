"""
Configuración central de la aplicación.

¿Por qué un único lugar para la configuración?
- Para no repartir valores mágicos (URLs, claves, tiempos) por todo el código.
- Para poder cambiar el comportamiento SIN tocar el código: solo el archivo .env.
- Para leer variables de entorno de forma tipada y validada gracias a Pydantic.

En la sustentación, si te piden "cambia la duración del token" o "apunta a otra
base de datos", el único archivo que se toca (o su .env) es este.
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Todas las variables de configuración del proyecto, con sus tipos.

    Pydantic las lee automáticamente desde:
      1. Variables de entorno del sistema.
      2. El archivo .env (ver model_config más abajo).
    Si falta una obligatoria o tiene un tipo inválido, la app falla al arrancar
    con un error claro (mejor que fallar a mitad de la demo).
    """

    # --- Base de datos ---
    # Por defecto SQLite (archivo local). Cambiando esta variable en .env se
    # migra a PostgreSQL sin tocar el código.
    DATABASE_URL: str = "sqlite:///./resenalibros.db"

    # --- Seguridad / JWT (se usará a fondo en la Fase 3) ---
    SECRET_KEY: str = "cambia-esto-por-una-clave-larga-y-secreta"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Aplicación ---
    PROJECT_NAME: str = "API Reseñas de Libros y Películas"
    DEBUG: bool = True

    # --- CORS ---
    # Orígenes (dominios) del frontend a los que se permite llamar a esta API
    # desde el navegador. NO van quemados en el código: se leen del .env para
    # poder cambiarlos sin tocar Python. Por defecto, los puertos típicos de
    # desarrollo de Vite (5173) y Create React App / Next (3000).
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _parsear_origenes(cls, valor: object) -> object:
        """Permite escribir la lista en .env separada por comas.

        Por defecto pydantic-settings esperaría un JSON (["...","..."]) para una
        lista. Este validador acepta también el formato cómodo separado por comas
        (BACKEND_CORS_ORIGINS=http://a.com,http://b.com) y lo convierte en lista.
        """
        if isinstance(valor, str) and not valor.startswith("["):
            return [origen.strip() for origen in valor.split(",") if origen.strip()]
        return valor

    # Le indica a Pydantic que lea el archivo .env; ignora variables extra que
    # no estén declaradas aquí (evita errores por variables del sistema ajenas).
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración como una única instancia (patrón singleton).

    @lru_cache asegura que el archivo .env se lea UNA sola vez y se reutilice,
    en lugar de releerlo en cada import. Se usa como función (y no como variable
    global) para poder sobrescribirla fácilmente en los tests más adelante.
    """
    return Settings()


# Instancia lista para importar en el resto del proyecto:  from app.core.config import settings
settings = get_settings()
