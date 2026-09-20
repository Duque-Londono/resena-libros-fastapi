"""
Pruebas de la lista de lectura / favoritos: acceso propio, idempotencia y aislamiento.
"""


def _registrar_y_headers(client, email, username):
    """Ayuda: registra un usuario y devuelve sus cabeceras de auth."""
    client.post(
        "/auth/register", json={"email": email, "username": username, "password": "clave12345"}
    )
    token = client.post(
        "/auth/login", data={"username": email, "password": "clave12345"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ver_lista_sin_token_devuelve_401(client):
    assert client.get("/me/reading-list").status_code == 401


def test_ver_lista_propia_vacia_devuelve_200(client, usuario_normal):
    respuesta = client.get("/me/reading-list", headers=usuario_normal["headers"])
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_anadir_obra_devuelve_201(client, usuario_normal, obra):
    respuesta = client.post(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    assert respuesta.status_code == 201


def test_anadir_duplicado_es_idempotente_devuelve_200(client, usuario_normal, obra):
    client.post(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    segunda = client.post(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    assert segunda.status_code == 200


def test_anadir_obra_inexistente_devuelve_404(client, usuario_normal):
    respuesta = client.post("/me/reading-list/999", headers=usuario_normal["headers"])
    assert respuesta.status_code == 404


def test_quitar_obra_devuelve_204(client, usuario_normal, obra):
    client.post(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    respuesta = client.delete(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    assert respuesta.status_code == 204


def test_quitar_obra_que_no_esta_devuelve_404(client, usuario_normal, obra):
    respuesta = client.delete(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    assert respuesta.status_code == 404


def test_aislamiento_entre_usuarios(client, usuario_normal, obra):
    # usuario_normal añade la obra a SU lista.
    client.post(f"/me/reading-list/{obra.id}", headers=usuario_normal["headers"])
    # Otro usuario distinto: su lista debe seguir vacía (no ve la del primero).
    otro = _registrar_y_headers(client, "otro@test.com", "otro")
    respuesta = client.get("/me/reading-list", headers=otro)
    assert respuesta.status_code == 200
    assert respuesta.json() == []
