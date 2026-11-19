"""
Consulta de calificaciones para el Admin y el Docente (solo lectura).
Las notas las calcula el sistema al presentar la evaluación (HU-15).
"""

from typing import List

from fastapi import APIRouter

from src.entities.usuario import Usuario
from src.schemas.calificacion_schema import CalificacionResponse
from src.services import calificacion as services_calificacion

from .deps import ADMIN_O_DOCENTE, DbSession

router = APIRouter(prefix="/calificaciones", tags=["calificaciones"])


@router.get("", response_model=List[CalificacionResponse])
def listar_calificaciones(db: DbSession, skip: int = 0, limit: int = 100, usuario: Usuario = ADMIN_O_DOCENTE):
    return services_calificacion.obtener_para_usuario(db, usuario, skip, limit)
