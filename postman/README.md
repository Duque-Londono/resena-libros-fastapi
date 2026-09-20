# Colección de Postman — ReseñaLibros API

Pruebas manuales y automatizadas de la API con Postman (o Newman, su versión de
línea de comandos).

## Archivos
- `ResenaLibros.postman_collection.json` — la colección (carpetas Auth, Works,
  Reviews, Reading list).
- `ResenaLibros.postman_environment.json` — el entorno con las variables
  `base_url`, `token`, `work_id`, `review_id`.

## Requisitos previos
1. Tener la API corriendo en `http://127.0.0.1:8000`:
   ```bash
   alembic upgrade head
   python -m app.db.seed        # crea el admin de la semilla (admin@demo.com / admin12345)
   uvicorn app.main:app --reload
   ```
   El login de la colección usa el **admin sembrado**, porque crear/editar obras
   requiere rol moderador o admin.

## Cómo importar
1. Abre Postman → **Import** → arrastra los dos archivos `.json`.
2. Arriba a la derecha, selecciona el entorno **"ReseñaLibros - Local"**.

## Cómo correr el flujo completo
- **Manual (uno a uno):** ejecuta en orden Auth → Works → Reviews → Reading list.
  El login guarda el `token`; crear obra guarda `work_id`; crear reseña guarda
  `review_id`. No hay que copiar nada a mano.
- **Automático (Collection Runner / Newman):**
  - En Postman: botón **Run** sobre la colección.
  - Con Newman (CLI):
    ```bash
    npx newman run postman/ResenaLibros.postman_collection.json \
        -e postman/ResenaLibros.postman_environment.json
    ```

## Detalles útiles
- **Autorización a nivel de colección:** `Bearer {{token}}`. Los requests
  protegidos la heredan; los públicos (register, login, GET de works/reviews)
  la sobrescriben con `noauth`.
- **Guardado automático de variables** (pestaña *Tests*):
  - Login → `pm.environment.set("token", pm.response.json().access_token)`.
  - Crear obra → `pm.environment.set("work_id", pm.response.json().id)`.
  - Crear reseña → `pm.environment.set("review_id", pm.response.json().id)`.
- **Flujo auto-curativo:** "DELETE Work" borra la obra creada. Para que un pase
  completo del Runner no se rompa, el *pre-request* de "POST Review" vuelve a
  crear una obra y actualiza `work_id`. Así la colección corre entera en verde
  cuantas veces se quiera (el registro acepta 201 la primera vez y 409 después).
