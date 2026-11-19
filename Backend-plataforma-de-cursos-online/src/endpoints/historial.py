"""
RF-07 Control de cambios (P7): historial de modificaciones de contenidos activos.
Solo lectura y solo para el Administrador. Los registros los escriben los servicios de
curso, lección, material, evaluación, pregunta y categoría al actualizar o eliminar.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.schemas.historial_schema import HistorialCambioResponse
from src.services import historial as services_historial

from .deps import SOLO_ADMIN, DbSession

router = APIRouter(prefix="/historial", tags=["historial de cambios"], dependencies=[SOLO_ADMIN])


def _respuesta(registro) -> HistorialCambioResponse:
    usuario = registro.usuario
    return HistorialCambioResponse(
        id_historial=registro.id_historial,
        entidad=registro.entidad,
        id_registro=registro.id_registro,
        nombre_registro=registro.nombre_registro,
        accion=registro.accion,
        detalle=registro.detalle,
        id_usuario=registro.id_usuario,
        nombre_usuario=usuario.nombre_usuario if usuario else None,
        rol_usuario=usuario.rol if usuario else None,
        fecha=registro.fecha,
    )


@router.get("", response_model=List[HistorialCambioResponse])
def listar_historial(
    db: DbSession,
    entidad: Optional[str] = None,
    id_usuario: Optional[UUID] = None,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    skip: int = 0,
    limit: int = 200,
):
    """Filtros opcionales: ?entidad=CURSO, ?id_usuario=..., ?desde=2026-11-01&hasta=2026-11-30."""
    try:
        registros = services_historial.buscar(db, entidad, id_usuario, desde, hasta, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return [_respuesta(r) for r in registros]
