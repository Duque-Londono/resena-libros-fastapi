# Pruebas E2E con Playwright — ReseñaLibros API

Pruebas de extremo a extremo que ejercitan la API real por HTTP (API request
context de Playwright), más un smoke test de que Swagger (`/docs`) carga.

## Requisitos previos: la API debe estar corriendo y sembrada
Estas pruebas NO levantan el servidor: asumen que la API está disponible en
`http://127.0.0.1:8000`. En otra terminal, desde la raíz del proyecto:

```bash
source .venv/bin/activate
alembic upgrade head          # crea las tablas
python -m app.db.seed         # crea el admin sembrado (admin@demo.com / admin12345)
uvicorn app.main:app          # deja la API corriendo en el puerto 8000
```

El flujo E2E inicia sesión como ese admin para poder crear obras (requiere rol
moderador/admin).

## Instalar y ejecutar (dentro de e2e/)
```bash
cd e2e
npm install                   # instala @playwright/test (versión fija)
npx playwright install         # descarga los navegadores (solo hace falta 1 vez)
npx playwright test           # ejecuta todas las pruebas
```

- `npm test` es un atajo de `playwright test`.
- `npx playwright test smoke` corre solo el smoke; `... flujo_resenas` solo el flujo.

## Qué se prueba
- `tests/smoke.spec.ts`: `GET /` (200), `GET /docs` (200 y contiene "swagger"),
  `GET /openapi.json` (200 y tiene la clave `paths`).
- `tests/flujo_resenas.spec.ts`: registro/login de usuario y admin, creación de
  obra, creación y lectura de reseña, edición por el dueño, bloqueo de edición
  ajena (403), favoritos y limpieza (borrado de la reseña).

Los emails de prueba llevan un timestamp para no colisionar entre ejecuciones,
así los tests se pueden correr repetidamente sin limpiar la base de datos.
