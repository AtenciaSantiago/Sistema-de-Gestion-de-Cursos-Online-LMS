"""
Dependencias que comparten todos los endpoints: la sesión de base de datos,
quién es el usuario del token y los permisos por rol.

Entregable 2 - Permisos por rol (RN-02 y RNF-03)
Antes casi todos los endpoints dejaban hacer cualquier cosa con solo tener
sesión (o sin ella): un estudiante podía ponerse nota, aprobarse o crear cursos.
Uso en un endpoint:   dependencies=[SOLO_ADMIN]   o   dependencies=[ADMIN_O_DOCENTE]
"""

from typing import Annotated, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.config import get_db
from src.entities.usuario import Usuario
from src.utils.jwt_utils import decode_jwt

DbSession = Annotated[Session, Depends(get_db)]
# Entregable 3: auto_error=False para responder nosotros, en español y siempre con 401,
# cuando la petición llega sin el encabezado Authorization (antes respondía FastAPI en inglés).
security = HTTPBearer(auto_error=False)

MENSAJE_SIN_PERMISO = "No tiene permisos para realizar esta acción"
MENSAJE_SIN_SESION = "Debe iniciar sesión para realizar esta acción"


def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Saca el id del usuario del token. Sin token, o con token vencido o falso -> 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MENSAJE_SIN_SESION,
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_jwt(credentials.credentials)["user_id"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def obtener_usuario_actual(db: DbSession, user_id: str = Depends(get_current_user_id)) -> Usuario:
    """El usuario dueño del token. Si el admin lo desactivó, pierde el acceso de inmediato (HU-03 esc. 3)."""
    try:
        id_usuario = UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return usuario


def requiere_rol(*roles: str):
    """Crea una dependencia que solo deja pasar a los roles indicados."""
    permitidos = {r.upper() for r in roles}

    def verificar(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
        if (usuario.rol or "").upper() not in permitidos:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_SIN_PERMISO)
        return usuario

    return verificar


SOLO_ADMIN = Depends(requiere_rol("ADMIN"))
ADMIN_O_DOCENTE = Depends(requiere_rol("ADMIN", "DOCENTE"))
SOLO_ESTUDIANTE = Depends(requiere_rol("ESTUDIANTE"))
