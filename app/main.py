"""
Punto de entrada de la aplicación FastAPI.

Aquí se crea la instancia `app`, se configuran metadatos (nombre, versión) y,
en fases posteriores, se montarán los routers (auth, works, reviews, listas).

Para levantar el servidor en desarrollo:
    uvicorn app.main:app --reload

Luego abre la documentación interactiva (Swagger) en:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth, works

# La instancia `app` es lo que uvicorn ejecuta (app.main:app).
# title/version alimentan la página /docs, para que la profesora pueda probar
# los endpoints cómodamente durante la sustentación.
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "API de red social para reseñar y calificar libros y películas. "
        "Proyecto académico de FastAPI."
    ),
)


@app.get("/", tags=["salud"])
def raiz() -> dict[str, str]:
    """Endpoint de bienvenida / comprobación rápida de que la API está viva.

    Sirve como 'health check' sencillo: si responde, el servidor arrancó bien.
    """
    return {
        "mensaje": "API de Reseñas funcionando",
        "documentacion": "/docs",
    }


# --- Routers ---
# Fase 3: autenticación (registro, login, perfil).
app.include_router(auth.router)
# Fase 4: catálogo de obras (libros/películas).
app.include_router(works.router)

# NOTA: Los routers de reseñas y listas de lectura se incluirán en las siguientes fases.
