"""
Pruebas de validación de Pydantic centradas en las FRONTERAS exactas.

Objetivo: comprobar que los límites están puestos con el operador correcto
(<=, >=), probando justo el valor válido del borde y el primer valor inválido.

Para las reseñas VÁLIDAS se registra un usuario nuevo en cada caso, porque la
regla "una reseña por usuario y obra" impediría reusar el mismo usuario sobre la
misma obra (daría 409, no un fallo de validación).
"""

import pytest


def _headers_usuario_unico(client, sufijo: str) -> dict:
    """Registra un usuario con email único (por sufijo) y devuelve sus headers."""
    email = f"val_{sufijo}@test.com"
    client.post(
        "/auth/register", json={"email": email, "username": f"val_{sufijo}", "password": "clave12345"}
    )
    token = client.post(
        "/auth/login", data={"username": email, "password": "clave12345"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Rating: válido en [1, 5]; inválido en 0 y 6 ---------------------------

@pytest.mark.parametrize("rating", [1, 5])
def test_rating_en_los_bordes_validos_es_aceptado(client, obra, rating):
    headers = _headers_usuario_unico(client, f"rating{rating}")
    respuesta = client.post(
        f"/works/{obra.id}/reviews", json={"rating": rating, "text": "ok"}, headers=headers
    )
    assert respuesta.status_code == 201


@pytest.mark.parametrize("rating", [0, 6])
def test_rating_fuera_de_rango_es_rechazado(client, obra, usuario_normal, rating):
    respuesta = client.post(
        f"/works/{obra.id}/reviews",
        json={"rating": rating, "text": "ok"},
        headers=usuario_normal["headers"],
    )
    assert respuesta.status_code == 422


# --- Texto: válido con longitud 1 y 2000; inválido con 0 y 2001 ------------

@pytest.mark.parametrize("longitud", [1, 2000])
def test_texto_en_los_bordes_validos_es_aceptado(client, obra, longitud):
    headers = _headers_usuario_unico(client, f"texto{longitud}")
    respuesta = client.post(
        f"/works/{obra.id}/reviews",
        json={"rating": 3, "text": "a" * longitud},
        headers=headers,
    )
    assert respuesta.status_code == 201


@pytest.mark.parametrize("longitud", [0, 2001])
def test_texto_fuera_de_rango_es_rechazado(client, obra, usuario_normal, longitud):
    respuesta = client.post(
        f"/works/{obra.id}/reviews",
        json={"rating": 3, "text": "a" * longitud},
        headers=usuario_normal["headers"],
    )
    assert respuesta.status_code == 422
