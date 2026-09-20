# Frontend de demostración

Frontend **de demostración** para consumir la API de Reseñas de Libros y Películas.
Es un único archivo (`index.html`) con **HTML + CSS + JavaScript vanilla**: sin
frameworks, sin build, sin npm. Está pensado para enseñar visualmente la API
durante la sustentación y para poder explicarse entero.

## Qué demuestra (los 4 pilares de la API)

1. **Autenticación**: login con JWT, perfil del usuario (`/auth/me`) y cerrar sesión.
2. **Catálogo**: listado público de obras (`/works`) con filtros por tipo y género.
3. **Reseñas**: ver reseñas de una obra y crear una nueva (con manejo de 409 y 422).
4. **Favoritos**: añadir obras a la lista de lectura y verla (`/me/reading-list`).
5. **Extra (solo admin)**: formulario para crear obras nuevas (`POST /works`).

## Requisito previo: la API tiene que estar corriendo y sembrada

Desde la **raíz del proyecto** (no desde `frontend/`):

```bash
# 1) Servidor de la API
uvicorn app.main:app --reload      # queda escuchando en http://127.0.0.1:8000

# 2) Datos de demostración (usuarios y catálogo). Ejecutar una vez.
python -m app.db.seed
```

## Cómo servir el frontend

⚠️ **No se abre con doble clic.** Abrir el archivo con `file://` rompe el CORS del
navegador y las peticiones a la API fallarán.

Hay que servirlo por HTTP en el **puerto 5173**, que ya está en los orígenes CORS
permitidos de la API. En **otra terminal**:

```bash
cd frontend
python -m http.server 5173
```

Luego abre en el navegador:

```
http://localhost:5173
```

## Credenciales de demo

| Rol     | Usuario / email                      | Contraseña   |
|---------|--------------------------------------|--------------|
| Admin   | `admin@demo.com` (o `admin`)         | `admin12345` |
| Usuario | `ana@demo.com` (o `ana`)             | `ana123456`  |

> El login admite **email o nombre de usuario** en el mismo campo.
> El formulario de crear obra solo aparece al entrar como **admin**.

## Cómo cambiar la URL de la API

En `index.html`, al inicio del `<script>`, está la constante:

```js
const API_URL = "http://127.0.0.1:8000";
```

Cámbiala ahí si la API se expone en otra dirección o puerto.

## Notas de diseño (por si preguntan)

- **El token JWT se guarda en memoria** (una variable JS), no en `localStorage`.
  Es lo más simple de explicar; al recargar la página se pierde la sesión, lo
  cual es aceptable en una demo.
- **El login usa `form-urlencoded`** (estándar OAuth2), por eso se envía con
  `URLSearchParams` y sin cabecera `Content-Type` manual. El resto de endpoints
  usan **JSON** con `Authorization: Bearer <token>`.
- Los errores se muestran en un **área de mensaje** en la interfaz (no `alert()`),
  distinguiendo 401 (sesión), 403 (permiso), 404, 409 (duplicado) y 422 (validación).
