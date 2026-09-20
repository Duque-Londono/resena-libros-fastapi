"""
Seguridad: hash de contraseñas (Argon2) y tokens JWT (PyJWT).

Este archivo concentra TODA la criptografía del proyecto en un solo lugar:
- Nunca se guardan contraseñas en texto plano, solo su hash Argon2.
- Los tokens JWT se firman con la SECRET_KEY y el algoritmo definidos en config.

¿Por qué estas librerías?
- pwdlib con Argon2: passlib está sin mantenimiento y se rompe con bcrypt 4.x.
- PyJWT: python-jose arrastra el CVE-2024-33663.
Son, además, las que recomienda hoy la documentación oficial de FastAPI.
"""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Gestor de contraseñas. .recommended() usa Argon2id (el estándar actual), con
# parámetros de coste seguros por defecto. Se crea una sola vez y se reutiliza.
_password_hash = PasswordHash.recommended()


# --- Contraseñas -----------------------------------------------------------

def hash_password(password: str) -> str:
    """Devuelve el hash Argon2 de una contraseña en texto plano.

    Se llama al REGISTRAR un usuario; el resultado es lo que se guarda en la
    columna users.hashed_password.
    """
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba si una contraseña en texto plano coincide con su hash.

    Se llama al INICIAR SESIÓN. Devuelve True/False sin lanzar excepción, para
    que quien llama decida la respuesta HTTP.
    """
    return _password_hash.verify(plain_password, hashed_password)


# --- Tokens JWT ------------------------------------------------------------

def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """Crea un JWT firmado que identifica al usuario.

    - `subject`: identificador del usuario (su id). Se guarda en el claim "sub".
      El estándar JWT exige que "sub" sea texto, por eso se convierte a str.
    - `expires_minutes`: minutos de validez; si es None, usa el valor de config.
      Tenerlo configurable permite cambiar la caducidad sin tocar el código.
    """
    if expires_minutes is None:
        expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),          # a quién pertenece el token
        "iat": ahora,                 # emitido en (issued at)
        "exp": ahora + timedelta(minutes=expires_minutes),  # expira en
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Verifica la firma y la caducidad del token y devuelve su contenido.

    Lanza `jwt.PyJWTError` (o subclase, como ExpiredSignatureError) si el token
    es inválido o caducó. Quien llama (get_current_user) captura ese error y
    responde 401. Aquí NO se decide la respuesta HTTP: este archivo solo hace
    criptografía, la capa de dependencias traduce a HTTP.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
