"""
Punto de entrada de la aplicación FastAPI.

Aquí se crea la instancia `app`, se configuran los middlewares (CORS y logging) y
se montan los routers (auth, works, reviews, listas de lectura).

Para levantar el servidor en desarrollo:
    uvicorn app.main:app --reload

Luego abre la documentación interactiva (Swagger) en:
    http://127.0.0.1:8000/docs
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, reading_lists, reviews, works

# Configuración básica de logging para ver las peticiones en consola durante la
# sustentación. En un proyecto real esto se afinaría (formato, destino, niveles).
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("api")

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

# ---------------------------------------------------------------------------
# MIDDLEWARE 1: CORS (Cross-Origin Resource Sharing)
# ---------------------------------------------------------------------------
# ¿Qué problema resuelve? Por seguridad, el navegador bloquea que una web servida
# en un origen (p. ej. http://localhost:5173, tu frontend) llame por fetch/AJAX a
# una API en OTRO origen (p. ej. http://localhost:8000, este backend). CORS es el
# mecanismo por el que el backend declara "confío en estos orígenes", y entonces
# el navegador permite la llamada. Sin esto, un frontend separado no podría
# consumir la API.
#
# Los orígenes permitidos vienen de la configuración (.env), NO quemados aquí.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # quién puede llamar
    allow_credentials=True,   # permite enviar cookies / cabecera Authorization
    allow_methods=["*"],      # DESARROLLO: todos los métodos (GET, POST, PUT...)
    allow_headers=["*"],      # DESARROLLO: todas las cabeceras
    # NOTA PRODUCCIÓN: conviene restringir allow_methods y allow_headers a lo
    # estrictamente necesario, y listar orígenes concretos (nunca "*" junto con
    # allow_credentials=True, que además el estándar prohíbe).
)


# ---------------------------------------------------------------------------
# MIDDLEWARE 2: logging + tiempo de proceso (didáctico)
# ---------------------------------------------------------------------------
# ¿Qué es un middleware? Es código que envuelve CADA petición: se ejecuta ANTES
# de que la petición llegue al endpoint y DESPUÉS de que este genera la respuesta.
# Sirve para tareas transversales (logging, autenticación global, métricas...).
#
# Orden de ejecución de este middleware:
#   1) Llega la petición  -> guardamos el instante de inicio (antes del endpoint).
#   2) call_next(request) -> ejecuta el endpoint y devuelve su respuesta.
#   3) Con la respuesta ya lista (después del endpoint) -> calculamos la duración,
#      la añadimos como cabecera X-Process-Time y registramos la línea de log.
@app.middleware("http")
async def registrar_peticiones(request: Request, call_next):
    inicio = time.perf_counter()  # (1) antes del endpoint

    response = await call_next(request)  # (2) ejecuta el endpoint

    # (3) después del endpoint
    duracion = time.perf_counter() - inicio
    # Se expone el tiempo en la respuesta para poder inspeccionarlo desde el cliente.
    response.headers["X-Process-Time"] = f"{duracion:.4f}"
    logger.info(
        "%s %s -> %s (%.4fs)",
        request.method,
        request.url.path,
        response.status_code,
        duracion,
    )
    return response


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
# Fase 5: reseñas y calificaciones.
app.include_router(reviews.router)
# Fase 6: listas de lectura / favoritos.
app.include_router(reading_lists.router)
