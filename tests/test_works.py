"""
Pruebas del catálogo de obras: lectura pública y escritura con permisos.
"""

OBRA_VALIDA = {"title": "Nueva obra", "type": "book", "genre": "fantasy", "release_year": 2020}


def test_listar_obras_es_publico(client, obra):
    respuesta = client.get("/works")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_ver_obra_por_id_es_publico(client, obra):
    respuesta = client.get(f"/works/{obra.id}")
    assert respuesta.status_code == 200
    assert respuesta.json()["title"] == obra.title


def test_ver_obra_inexistente_devuelve_404(client):
    respuesta = client.get("/works/999")
    assert respuesta.status_code == 404


def test_crear_obra_sin_token_devuelve_401(client):
    respuesta = client.post("/works", json=OBRA_VALIDA)
    assert respuesta.status_code == 401


def test_crear_obra_con_usuario_normal_devuelve_403(client, usuario_normal):
    respuesta = client.post("/works", json=OBRA_VALIDA, headers=usuario_normal["headers"])
    assert respuesta.status_code == 403


def test_crear_obra_con_moderator_devuelve_201(client, moderator):
    respuesta = client.post("/works", json=OBRA_VALIDA, headers=moderator["headers"])
    assert respuesta.status_code == 201


def test_crear_obra_con_admin_devuelve_201(client, admin):
    respuesta = client.post("/works", json=OBRA_VALIDA, headers=admin["headers"])
    assert respuesta.status_code == 201


def test_crear_obra_anio_invalido_devuelve_422(client, admin):
    payload = {**OBRA_VALIDA, "release_year": 3000}
    respuesta = client.post("/works", json=payload, headers=admin["headers"])
    assert respuesta.status_code == 422


def test_crear_obra_genero_invalido_devuelve_422(client, admin):
    payload = {**OBRA_VALIDA, "genre": "inventado"}
    respuesta = client.post("/works", json=payload, headers=admin["headers"])
    assert respuesta.status_code == 422


def test_put_parcial_conserva_los_demas_campos(client, admin, obra):
    # Solo se envía release_year; el título debe conservarse.
    respuesta = client.put(
        f"/works/{obra.id}", json={"release_year": 1999}, headers=admin["headers"]
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["release_year"] == 1999
    assert datos["title"] == obra.title  # no se perdió


def test_borrar_obra_devuelve_204_y_luego_404(client, admin, obra):
    borrado = client.delete(f"/works/{obra.id}", headers=admin["headers"])
    assert borrado.status_code == 204
    # Tras borrarla, ya no existe.
    assert client.get(f"/works/{obra.id}").status_code == 404


def test_borrar_obra_inexistente_devuelve_404(client, admin):
    respuesta = client.delete("/works/999", headers=admin["headers"])
    assert respuesta.status_code == 404
