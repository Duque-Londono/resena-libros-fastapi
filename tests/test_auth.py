"""
Pruebas de autenticación: registro, login y perfil.
Cada test comprueba UN comportamiento concreto (una sola responsabilidad).
"""


def test_registro_devuelve_201_y_no_expone_password(client):
    respuesta = client.post(
        "/auth/register",
        json={"email": "nuevo@test.com", "username": "nuevo", "password": "clave12345"},
    )
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["email"] == "nuevo@test.com"
    # La respuesta NUNCA debe incluir la contraseña ni su hash.
    assert "password" not in datos
    assert "hashed_password" not in datos


def test_registro_email_duplicado_devuelve_409(client, usuario_normal):
    # usuario_normal ya existe con email user@test.com
    respuesta = client.post(
        "/auth/register",
        json={"email": "user@test.com", "username": "otro", "password": "clave12345"},
    )
    assert respuesta.status_code == 409


def test_registro_username_duplicado_devuelve_409(client, usuario_normal):
    respuesta = client.post(
        "/auth/register",
        json={"email": "distinto@test.com", "username": "usuario", "password": "clave12345"},
    )
    assert respuesta.status_code == 409


def test_registro_password_corta_devuelve_422(client):
    respuesta = client.post(
        "/auth/register",
        json={"email": "x@test.com", "username": "equis", "password": "corta"},
    )
    assert respuesta.status_code == 422


def test_registro_ignora_el_rol_enviado_y_crea_usuario_normal(client):
    # Aunque el cliente intente colar role=admin, el schema no lo acepta y el
    # usuario se crea como USER. Se comprueba consultando /auth/me.
    client.post(
        "/auth/register",
        json={"email": "listo@test.com", "username": "listillo", "password": "clave12345", "role": "admin"},
    )
    token = client.post(
        "/auth/login", data={"username": "listo@test.com", "password": "clave12345"}
    ).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "user"


def test_login_correcto_devuelve_token(client, usuario_normal):
    respuesta = client.post(
        "/auth/login", data={"username": "user@test.com", "password": "password123"}
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["token_type"] == "bearer"
    assert datos["access_token"]  # no vacío


def test_login_credenciales_malas_devuelve_401(client, usuario_normal):
    respuesta = client.post(
        "/auth/login", data={"username": "user@test.com", "password": "incorrecta"}
    )
    assert respuesta.status_code == 401


def test_me_con_token_devuelve_datos(client, usuario_normal):
    respuesta = client.get("/auth/me", headers=usuario_normal["headers"])
    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "user@test.com"


def test_me_sin_token_devuelve_401(client):
    respuesta = client.get("/auth/me")
    assert respuesta.status_code == 401


def test_me_con_token_malformado_devuelve_401(client):
    # Un token que no es un JWT válido debe rechazarse (rama de error del decode).
    respuesta = client.get("/auth/me", headers={"Authorization": "Bearer esto-no-es-un-jwt"})
    assert respuesta.status_code == 401


def test_me_con_token_de_usuario_inexistente_devuelve_401(client):
    # Token firmado correctamente pero para un id que no existe en la BD.
    from app.core.security import create_access_token

    token = create_access_token(subject=99999)
    respuesta = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 401
