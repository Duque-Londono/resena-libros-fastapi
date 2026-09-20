# 📚 ReseñaLibros API

API de red social para **reseñar y calificar libros y películas**: catálogo de
obras, reseñas con calificación, listas de lectura/favoritos, autenticación con
JWT y roles de usuario. Proyecto académico construido con FastAPI, con foco en
código limpio, modular y fácil de sustentar.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)
![Tests](https://img.shields.io/badge/tests-53%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)

---

## Índice
1. [Características](#-características)
2. [Stack tecnológico](#-stack-tecnológico)
3. [Estructura del proyecto](#-estructura-del-proyecto)
4. [Requisitos previos](#-requisitos-previos)
5. [Instalación](#-instalación)
6. [Ejecución](#-ejecución)
7. [Credenciales de demo](#-credenciales-de-demo)
8. [Documentación de endpoints](#-documentación-de-endpoints)
9. [Modelo de datos](#-modelo-de-datos)
10. [Pruebas](#-pruebas)
11. [Notas de seguridad](#-notas-de-seguridad)
12. [Licencia y autor](#-licencia-y-autor)

---

## ✨ Características
- **Autenticación con JWT** y control de acceso por **roles** (`user` < `moderator` < `admin`).
- **CRUD del catálogo** de obras (libros/películas); crear/editar/eliminar solo para moderador o admin.
- **Reseñas y calificaciones** con **reglas de propiedad**: cada usuario edita/borra solo lo suyo; el admin puede sobre cualquiera.
- **Una reseña por usuario y obra** garantizada a nivel de BD (responde **409** al duplicar).
- **Listas de lectura / favoritos** privadas por usuario (aislamiento total).
- **Validación con Pydantic v2**: puntuación 1–5, límite de texto, géneros/tipos con `Enum`, ejemplos en Swagger.
- **CORS** configurable por entorno y **middleware** de logging con cabecera `X-Process-Time`.
- **Migraciones con Alembic** y **suite de pruebas** completa (pytest + Postman + Playwright).

---

## 🛠 Stack tecnológico

| Herramienta | Uso | Por qué |
|---|---|---|
| **FastAPI** | Framework web | Rápido, tipado, genera Swagger automáticamente. |
| **Pydantic v2** | Validación de datos | Validación declarativa y ejemplos para la documentación. |
| **SQLAlchemy 2.0** | ORM (síncrono) | Estilo moderno con `Mapped[]`; separación clara modelo/tabla. |
| **Alembic** | Migraciones | Vía **oficial** para crear/actualizar el esquema de forma versionada. |
| **PyJWT** | Tokens JWT | Se elige **en lugar de python-jose**, que arrastra el CVE-2024-33663. |
| **pwdlib + Argon2** | Hash de contraseñas | Se elige **en lugar de passlib** (sin mantenimiento y roto con bcrypt 4.x); Argon2id es el estándar actual. |
| **SQLite → PostgreSQL** | Base de datos | SQLite para desarrollo/demo sin instalar nada; cambiar a Postgres es **solo** editar `DATABASE_URL` en `.env`. |
| **pytest / Newman / Playwright** | Pruebas | Integración, colección HTTP y E2E, respectivamente. |

Todas las dependencias están **fijadas a versiones exactas** en `requirements.txt`
para que la instalación sea reproducible.

---

## 📁 Estructura del proyecto

```
ReseñaLibros_FastAPI/
├── app/
│   ├── main.py                 # App FastAPI: middlewares (CORS, logging) y routers
│   ├── core/
│   │   ├── config.py           # Configuración (pydantic-settings, lee .env)
│   │   ├── security.py         # Hash Argon2 + crear/verificar JWT
│   │   └── dependencies.py     # get_current_user + jerarquía de roles (un solo lugar)
│   ├── db/
│   │   ├── base.py             # Base declarativa (SQLAlchemy 2.0)
│   │   ├── session.py          # engine, SessionLocal, get_db, PRAGMA foreign_keys
│   │   └── seed.py             # Datos de demo idempotentes (admin, usuario, 5 obras)
│   ├── models/                 # Tablas ORM: user, work, review, reading_list, enums
│   ├── schemas/                # Modelos Pydantic (entrada/salida) por recurso
│   ├── crud/                   # Lógica de acceso a datos (routers finos)
│   └── routers/                # Endpoints: auth, works, reviews, reading_lists
├── alembic/                    # Migraciones (env.py lee la URL desde config)
│   └── versions/               # Migración inicial (4 tablas)
├── tests/                      # pytest: conftest + 5 archivos de test
├── postman/                    # Colección + entorno + README (Newman)
├── e2e/                        # Playwright: smoke + flujo E2E (TypeScript)
├── requirements.txt            # Dependencias con versiones fijas
├── .env.example                # Plantilla de variables (sin secretos)
├── alembic.ini
└── pytest.ini
```

---

## ✅ Requisitos previos
- **Python 3.14** (probado en 3.14).
- **pip** y **venv**.
- (Opcional) **Node.js** para las pruebas E2E con Playwright y Newman.

---

## 🚀 Instalación

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/Duque-Londono/resena-libros-fastapi.git
cd resena-libros-fastapi

# 2. Crear y activar el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias (versiones fijas)
pip install -r requirements.txt

# 4. Crear el archivo de configuración a partir de la plantilla
cp .env.example .env
#   (edita SECRET_KEY con una clave larga; puedes generarla con:
#    python -c "import secrets; print(secrets.token_hex(32))")

# 5. Crear las tablas con Alembic
alembic upgrade head

# 6. Sembrar datos de demo (admin + usuario + 5 obras)
python -m app.db.seed
```

---

## ▶️ Ejecución

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- **Swagger UI (documentación interactiva):** `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Esquema OpenAPI: `http://127.0.0.1:8000/openapi.json`

En Swagger, usa el botón **Authorize** para pegar el token del login y probar los
endpoints protegidos.

---

## 🔑 Credenciales de demo
Creadas por `python -m app.db.seed`:

| Rol | Usuario (email) | Contraseña |
|---|---|---|
| Administrador | `admin@demo.com` | `admin12345` |
| Usuario normal | `ana@demo.com` | `ana123456` |

> El login acepta **email o nombre de usuario** en el campo `username`.

---

## 📡 Documentación de endpoints

### Autenticación — `/auth`
| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| POST | `/auth/register` | Público | Registra un usuario (rol `user`). 409 si el email/username ya existe. |
| POST | `/auth/login` | Público | Devuelve un JWT (formulario OAuth2). |
| GET | `/auth/me` | Autenticado | Perfil del usuario actual (sin la contraseña). |

### Catálogo de obras — `/works`
| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| GET | `/works` | Público | Lista con paginación y filtros por `type`/`genre`. |
| GET | `/works/{id}` | Público | Detalle de una obra. 404 si no existe. |
| POST | `/works` | Moderador/Admin | Crea una obra. |
| PUT | `/works/{id}` | Moderador/Admin | Actualiza (parcial). |
| DELETE | `/works/{id}` | Moderador/Admin | Elimina. 204. |

### Reseñas — `/reviews` y `/works/{id}/reviews`
| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| GET | `/works/{id}/reviews` | Público | Reseñas de una obra (paginado). |
| POST | `/works/{id}/reviews` | Autenticado | Crea una reseña. 409 si ya reseñó esa obra. |
| GET | `/reviews/{id}` | Público | Detalle de una reseña. |
| PUT | `/reviews/{id}` | Dueño o Admin | Edita. 403 si no eres el autor ni admin. |
| DELETE | `/reviews/{id}` | Dueño o Admin | Elimina. 204. |

### Lista de lectura / favoritos — `/me/reading-list`
| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| GET | `/me/reading-list` | Autenticado | Ve **tu** lista (nunca la de otro). |
| POST | `/me/reading-list/{work_id}` | Autenticado | Añade una obra (idempotente: 201/200). 404 si la obra no existe. |
| DELETE | `/me/reading-list/{work_id}` | Autenticado | Quita una obra. 404 si no estaba. |

---

## 🗃 Modelo de datos

**Entidades y relaciones:**
- **User** `1 —— N` **Review** (un usuario escribe muchas reseñas).
- **Work** `1 —— N` **Review** (una obra recibe muchas reseñas).
- **User** `N —— M` **Work** a través de la tabla puente **reading_list** (favoritos).
- **Review** tiene una restricción **única** `(user_id, work_id)`: una reseña por usuario y obra.

```
User ─1───N─ Review ─N───1─ Work
User ─N──(reading_list)──N─ Work
```

Enums centralizados: `Role` (user/moderator/admin), `WorkType` (book/movie),
`Genre` (fiction, fantasy, science_fiction, …). Se guardan por **valor** en la BD.

---

## 🧪 Pruebas

### 1) Integración con pytest (+ cobertura)
```bash
source .venv/bin/activate
pytest                       # 53 tests
pytest --cov=app --cov-report=term-missing   # con cobertura (~90%)
```
BD de test **aislada** (SQLite en memoria), con `foreign_keys=ON` y una sola
sesión compartida entre las fixtures y el cliente.

### 2) Colección de Postman (Newman)
Con la API corriendo y sembrada:
```bash
npx newman run postman/ResenaLibros.postman_collection.json \
    -e postman/ResenaLibros.postman_environment.json
```
Flujo completo con guardado automático de `token`, `work_id`, `review_id`
(17 requests, 23 assertions). Ver `postman/README.md`.

### 3) E2E con Playwright
Con la API corriendo y sembrada, en otra terminal:
```bash
cd e2e
npm install
npx playwright test          # 4 tests: smoke (/docs) + flujo completo por API
```
Ver `e2e/README.md`.

---

## 🔒 Notas de seguridad
- **Contraseñas** hasheadas con **Argon2id** (pwdlib); nunca se guardan en texto plano.
- **JWT** firmados con `SECRET_KEY` (config); expiración configurable.
- El schema de salida **nunca expone** `hashed_password`.
- **Autor no suplantable**: en las reseñas y favoritos el usuario sale del token, no del body ni de la ruta.
- **Reglas de propiedad** centralizadas en un único helper (dueño o admin).
- **CORS** con orígenes definidos por entorno (no quemados); en producción se restringen métodos/cabeceras.
- `SECRET_KEY` y la base de datos **no se versionan** (`.gitignore`); se comparte solo `.env.example`.

> Nota: SQLite y las credenciales de demo son para desarrollo/sustentación. En
> producción: PostgreSQL, `SECRET_KEY` fuerte y orígenes CORS concretos.

---

## 📄 Licencia y autor
- **Licencia:** MIT.
- **Autor:** proyecto académico de la materia de FastAPI.

Construido con FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic.
