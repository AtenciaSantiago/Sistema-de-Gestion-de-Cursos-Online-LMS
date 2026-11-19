"""
Endpoints del aula virtual del estudiante (HU-12) y descarga del certificado (HU-13).
Solo para usuarios con rol Estudiante.
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from src.entities.usuario import Usuario
from src.services import aula as servicio_aula
from src.services import certificado as servicio_certificados

from .deps import SOLO_ESTUDIANTE, DbSession

router = APIRouter(prefix="/mis-cursos", tags=["aula virtual (estudiante)"])


@router.get("", response_model=List[Dict[str, Any]])
def listar_mis_cursos(db: DbSession, usuario: Usuario = SOLO_ESTUDIANTE):
    return servicio_aula.mis_cursos(db, usuario.id_usuario)


@router.get("/{id_curso}", response_model=Dict[str, Any])
def ver_contenido_del_curso(db: DbSession, id_curso: UUID, usuario: Usuario = SOLO_ESTUDIANTE):
    try:
        return servicio_aula.contenido_curso(db, usuario.id_usuario, id_curso)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/lecciones/{id_leccion}/completar", response_model=Dict[str, Any])
def marcar_leccion_completada(db: DbSession, id_leccion: UUID, usuario: Usuario = SOLO_ESTUDIANTE):
    try:
        avance, estado_curso = servicio_aula.marcar_completada(db, usuario.id_usuario, id_leccion)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    mensaje = "Lección marcada como completada"
    if estado_curso:  # HU-16: con esta lección se cerró el curso
        mensaje += f". Terminaste el curso: {estado_curso}"
    return {"porcentaje_avance": avance, "mensaje": mensaje, "estado_curso": estado_curso}


@router.get("/{id_curso}/certificado")
def descargar_certificado(db: DbSession, id_curso: UUID, usuario: Usuario = SOLO_ESTUDIANTE):
    """HU-13: descarga el certificado en PDF (solo con inscripción APROBADA)."""
    try:
        pdf, codigo = servicio_certificados.generar_documento(db, usuario.id_usuario, id_curso)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="certificado-{codigo}.pdf"'},
    )
