"""
Pruebas de reseñas: creación, unicidad, validación y reglas de propiedad.
"""


def _crear_resena(client, headers, work_id, rating=5, text="Muy buena obra"):
    """Ayuda: crea una reseña vía API y devuelve la respuesta."""
    return client.post(
        f"/works/{work_id}/reviews", json={"rating": rating, "text": text}, headers=headers
    )


def _registrar_y_headers(client, email, username):
    """Ayuda: registra un usuario nuevo y devuelve sus cabeceras de auth."""
    client.post(
        "/auth/register", json={"email": email, "username": username, "password": "clave12345"}
    )
    token = client.post(
        "/auth/login", data={"username": email, "password": "clave12345"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_crear_resena_devuelve_201(client, usuario_normal, obra):
    respuesta = _crear_resena(client, usuario_normal["headers"], obra.id)
    assert respuesta.status_code == 201
    assert respuesta.json()["rating"] == 5


def test_resena_duplicada_devuelve_409(client, usuario_normal, obra):
    _crear_resena(client, usuario_normal["headers"], obra.id)
    segunda = _crear_resena(client, usuario_normal["headers"], obra.id)
    assert segunda.status_code == 409


def test_rating_0_devuelve_422(client, usuario_normal, obra):
    assert _crear_resena(client, usuario_normal["headers"], obra.id, rating=0).status_code == 422


def test_rating_6_devuelve_422(client, usuario_normal, obra):
    assert _crear_resena(client, usuario_normal["headers"], obra.id, rating=6).status_code == 422


def test_texto_vacio_devuelve_422(client, usuario_normal, obra):
    assert _crear_resena(client, usuario_normal["headers"], obra.id, text="").status_code == 422


def test_texto_demasiado_largo_devuelve_422(client, usuario_normal, obra):
    texto = "a" * 2001  # supera el máximo de 2000
    assert _crear_resena(client, usuario_normal["headers"], obra.id, text=texto).status_code == 422


def test_crear_resena_en_obra_inexistente_devuelve_404(client, usuario_normal):
    assert _crear_resena(client, usuario_normal["headers"], 999).status_code == 404


def test_crear_resena_sin_token_devuelve_401(client, obra):
    respuesta = client.post(f"/works/{obra.id}/reviews", json={"rating": 5, "text": "x"})
    assert respuesta.status_code == 401


def test_editar_resena_ajena_devuelve_403(client, usuario_normal, obra):
    # usuario_normal crea la reseña; otro usuario intenta editarla.
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    otro = _registrar_y_headers(client, "otro@test.com", "otro")
    respuesta = client.put(f"/reviews/{resena_id}", json={"rating": 1}, headers=otro)
    assert respuesta.status_code == 403


def test_dueno_edita_su_resena_devuelve_200(client, usuario_normal, obra):
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    respuesta = client.put(
        f"/reviews/{resena_id}", json={"rating": 3}, headers=usuario_normal["headers"]
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["rating"] == 3


def test_admin_edita_resena_ajena_ok(client, usuario_normal, admin, obra):
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    respuesta = client.put(
        f"/reviews/{resena_id}", json={"text": "editada por admin"}, headers=admin["headers"]
    )
    assert respuesta.status_code == 200


def test_admin_borra_resena_ajena_ok(client, usuario_normal, admin, obra):
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    respuesta = client.delete(f"/reviews/{resena_id}", headers=admin["headers"])
    assert respuesta.status_code == 204


def test_moderator_no_puede_editar_resena_ajena_devuelve_403(client, usuario_normal, moderator, obra):
    # Clave: el moderator manda sobre el catálogo, NO sobre reseñas ajenas.
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    respuesta = client.put(
        f"/reviews/{resena_id}", json={"rating": 1}, headers=moderator["headers"]
    )
    assert respuesta.status_code == 403


def test_moderator_no_puede_borrar_resena_ajena_devuelve_403(client, usuario_normal, moderator, obra):
    resena_id = _crear_resena(client, usuario_normal["headers"], obra.id).json()["id"]
    respuesta = client.delete(f"/reviews/{resena_id}", headers=moderator["headers"])
    assert respuesta.status_code == 403
