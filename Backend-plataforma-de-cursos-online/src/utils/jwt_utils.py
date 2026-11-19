"""
Tokens de sesión (JWT) - HU-01 y RNF-03.

Cuando el usuario inicia sesión se le entrega un token firmado con SECRET_KEY.
En cada petición el token dice quién es (user_id) y vence a las 2 horas.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM") or "HS256"
DURACION_TOKEN = timedelta(hours=2)

# Entregable 2: sin clave secreta no se pueden firmar sesiones; mejor avisarlo al arrancar
# que fallar en pleno inicio de sesión
if not SECRET_KEY:
    raise ValueError("Se requiere SECRET_KEY en el archivo .env")


def create_token(user_id: str) -> str:
    """Crea el token de sesión del usuario."""
    payload = {"user_id": user_id, "exp": datetime.now(timezone.utc) + DURACION_TOKEN}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    """Lee el token. Si es falso o ya venció, PyJWT lanza un error (el endpoint responde 401)."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
