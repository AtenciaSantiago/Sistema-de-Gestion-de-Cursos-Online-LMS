"""
Endpoints de preguntas (HU-14, docente) y presentación de evaluaciones (HU-15, estudiante).
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from src.entities.usuario import Usuario
from src.schemas.pregunta_schema import (
    PreguntaCreate,
    PreguntaDocenteResponse,
    PreguntaEstudianteResponse,
    PreguntaUpdate,
    PresentarEvaluacionRequest,
    ResultadoEvaluacionResponse,
)
from src.schemas.response_schema import RespuestaAPI
from src.services import pregunta as servicio_preguntas
from src.services import presentacion_evaluacion as servicio_presentacion
from src.services.evaluacion import evaluacion_editable, obtener_por_id
from src.services.permisos import curso_de_evaluacion, puede_gestionar_curso

from .deps import ADMIN_O_DOCENTE, SOLO_ESTUDIANTE, DbSession

router = APIRouter(tags=["preguntas y presentación"])


def _error(e: Exception) -> HTTPException:
    codigo = status.HTTP_403_FORBIDDEN if isinstance(e, PermissionError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=codigo, detail=str(e))


# ----------------------------- Docente (HU-14) -----------------------------

@router.post("/evaluaciones/{id_evaluacion}/preguntas", response_model=PreguntaDocenteResponse, status_code=status.HTTP_201_CREATED)
def crear_pregunta(db: DbSession, id_evaluacion: UUID, dato: PreguntaCreate, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        return servicio_preguntas.crear(db, id_evaluacion, dato.model_dump(), usuario)
    except (PermissionError, ValueError) as e:
        raise _error(e)


@router.get("/evaluaciones/{id_evaluacion}/preguntas/clave", response_model=List[PreguntaDocenteResponse])
def listar_preguntas_con_clave(db: DbSession, id_evaluacion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    """El docente ve las preguntas CON la respuesta correcta (solo las de sus cursos)."""
    evaluacion = obtener_por_id(db, id_evaluacion)
    if not evaluacion or not puede_gestionar_curso(usuario, curso_de_evaluacion(db, evaluacion)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada")
    return servicio_preguntas.listar_por_evaluacion(db, id_evaluacion)


@router.put("/preguntas/{id_pregunta}", response_model=PreguntaDocenteResponse)
def actualizar_pregunta(db: DbSession, id_pregunta: UUID, dato: PreguntaUpdate, usuario: Usuario = ADMIN_O_DOCENTE):
    """HU-14 esc. 2: cambiar la clave u otros datos mientras nadie la haya presentado."""
    try:
        pregunta = servicio_preguntas.actualizar(db, id_pregunta, dato.model_dump(exclude_unset=True), usuario)
    except (PermissionError, ValueError) as e:
        raise _error(e)
    if not pregunta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    return pregunta


@router.delete("/preguntas/{id_pregunta}", response_model=RespuestaAPI)
def eliminar_pregunta(db: DbSession, id_pregunta: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    try:
        eliminada = servicio_preguntas.eliminar(db, id_pregunta, usuario)
    except (PermissionError, ValueError) as e:
        raise _error(e)
    if not eliminada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pregunta no encontrada")
    return RespuestaAPI(mensaje="Pregunta eliminada exitosamente", exito=True)


@router.get("/evaluaciones/{id_evaluacion}/editable")
def evaluacion_se_puede_editar(db: DbSession, id_evaluacion: UUID, usuario: Usuario = ADMIN_O_DOCENTE):
    """Para que la pantalla del docente deshabilite los botones si ya la presentaron (HU-14 esc. 2)."""
    try:
        evaluacion_editable(db, id_evaluacion, usuario)
        return {"editable": True, "mensaje": None}
    except PermissionError as e:
        raise _error(e)
    except ValueError as e:
        return {"editable": False, "mensaje": str(e)}


# ----------------------------- Estudiante (HU-15) -----------------------------

@router.get("/evaluaciones/{id_evaluacion}/preguntas", response_model=List[PreguntaEstudianteResponse])
def listar_preguntas_para_presentar(db: DbSession, id_evaluacion: UUID, usuario: Usuario = SOLO_ESTUDIANTE):
    """El estudiante recibe las preguntas SIN la respuesta correcta (solo con inscripción ACTIVA)."""
    try:
        return servicio_presentacion.preguntas_para_presentar(db, id_evaluacion, usuario.id_usuario)
    except (PermissionError, ValueError) as e:
        raise _error(e)


@router.get("/evaluaciones/{id_evaluacion}/mi-resultado", response_model=Dict[str, Any])
def ver_mi_resultado(db: DbSession, id_evaluacion: UUID, usuario: Usuario = SOLO_ESTUDIANTE):
    """HU-15 esc. 3: resultado anterior en modo de solo lectura, con todos sus intentos."""
    try:
        return servicio_presentacion.mi_resultado(db, id_evaluacion, usuario.id_usuario)
    except (PermissionError, ValueError) as e:
        raise _error(e)


@router.post("/evaluaciones/{id_evaluacion}/presentar", response_model=ResultadoEvaluacionResponse)
def presentar_evaluacion(db: DbSession, id_evaluacion: UUID, dato: PresentarEvaluacionRequest, usuario: Usuario = SOLO_ESTUDIANTE):
    try:
        resultado = servicio_presentacion.presentar(db, id_evaluacion, usuario.id_usuario, dato.respuestas)
    except (PermissionError, ValueError) as e:
        raise _error(e)

    if resultado.aprobada:
        mensaje = "¡Aprobaste la evaluación! La lección quedó aprobada."  # HU-15 esc. 1
    else:
        mensaje = "No alcanzaste la nota mínima requerida. Puedes volver a intentarlo."  # HU-15 esc. 2
    return ResultadoEvaluacionResponse(**resultado.__dict__, mensaje=mensaje)
