"""
Inscripciones para el Administrador (RF-10 y auditoría de cierres RF-18).
El Admin NO puede aprobar ni reprobar: eso lo hace el sistema (HU-16).
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.inscripcion_schema import InscripcionCreate, InscripcionResponse
from src.services import inscripcion as services_inscripcion

from .deps import SOLO_ADMIN, DbSession

router = APIRouter(prefix="/inscripciones", tags=["inscripciones"])


def _respuesta(db, inscripcion) -> InscripcionResponse:
    base = InscripcionResponse.model_validate(inscripcion).model_dump()
    base.update(
        nombre_curso=inscripcion.curso.nombre_curso if inscripcion.curso else None,
        nombre_estudiante=inscripcion.usuario_inscrito.nombre_usuario if inscripcion.usuario_inscrito else None,
        **services_inscripcion.datos_de_cierre(db, inscripcion),
    )
    return InscripcionResponse(**base)


@router.get("", response_model=List[InscripcionResponse])
def listar_inscripciones(
    db: DbSession, estado: Optional[str] = None, skip: int = 0, limit: int = 100, admin: Usuario = SOLO_ADMIN
):
    """Filtro opcional por estado (ej. ?estado=APROBADA) para auditar los cierres académicos."""
    try:
        inscripciones = services_inscripcion.obtener_todos(db, estado, skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return [_respuesta(db, i) for i in inscripciones]


@router.get("/cierres", response_model=List[InscripcionResponse])
def reporte_de_cierres(db: DbSession, estado: Optional[str] = None, admin: Usuario = SOLO_ADMIN):
    """HU-17: cursos ya cerrados con su promedio y el código del certificado (filtro opcional por estado)."""
    try:
        return [_respuesta(db, i) for i in services_inscripcion.cierres(db, estado)]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id_inscripcion}", response_model=InscripcionResponse)
def obtener_inscripcion(db: DbSession, id_inscripcion: UUID, admin: Usuario = SOLO_ADMIN):
    inscripcion = services_inscripcion.obtener_por_id(db, id_inscripcion)
    if not inscripcion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada")
    return _respuesta(db, inscripcion)


@router.post("", response_model=InscripcionResponse, status_code=status.HTTP_201_CREATED)
def matricular_manualmente(db: DbSession, dato: InscripcionCreate, admin: Usuario = SOLO_ADMIN):
    try:
        inscripcion = services_inscripcion.matricular_manual(db, admin, dato.id_curso, dato.id_usuario_inscrito)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return _respuesta(db, inscripcion)


@router.put("/{id_inscripcion}/cancelar", response_model=InscripcionResponse)
def cancelar_inscripcion(db: DbSession, id_inscripcion: UUID, admin: Usuario = SOLO_ADMIN):
    try:
        inscripcion = services_inscripcion.cancelar(db, id_inscripcion, admin)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not inscripcion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inscripción no encontrada")
    return _respuesta(db, inscripcion)
