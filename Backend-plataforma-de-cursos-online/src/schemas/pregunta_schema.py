from typing import Dict, List, Optional
from uuid import UUID

from pydantic import ConfigDict, BaseModel, Field

from src.schemas.base_schema import EntradaSchema


class PreguntaCreate(EntradaSchema):
    """Lo que manda el docente para crear una pregunta (HU-14)."""

    tipo: str = Field(..., examples=["OPCION_MULTIPLE", "VERDADERO_FALSO"])
    enunciado: str
    opciones: List[str] = []  # en verdadero/falso se ignoran: siempre son Verdadero y Falso
    respuesta_correcta: str
    orden: Optional[int] = None


class PreguntaUpdate(EntradaSchema):
    """HU-14 esc. 2: el docente corrige el enunciado, las opciones o la clave (el tipo no cambia)."""

    enunciado: Optional[str] = None
    opciones: Optional[List[str]] = None
    respuesta_correcta: Optional[str] = None
    orden: Optional[int] = None


class PreguntaDocenteResponse(BaseModel):
    """Lo que ve el docente: incluye la respuesta correcta."""

    id_pregunta: UUID
    id_evaluacion: UUID
    tipo: str
    enunciado: str
    opciones: List[str]
    respuesta_correcta: str
    orden: int

    model_config = ConfigDict(from_attributes=True)


class PreguntaEstudianteResponse(BaseModel):
    """Lo que ve el estudiante: SIN la respuesta correcta."""

    id_pregunta: UUID
    tipo: str
    enunciado: str
    opciones: List[str]
    orden: int

    model_config = ConfigDict(from_attributes=True)


class PresentarEvaluacionRequest(EntradaSchema):
    """Respuestas del estudiante: {id_pregunta: opción elegida}."""

    respuestas: Dict[str, str]


class ResultadoEvaluacionResponse(BaseModel):
    id_inscripcion: UUID
    id_evaluacion: UUID
    correctas: int
    total: int
    nota: float
    nota_minima: float
    aprobada: bool
    numero_intento: int  # RF-13: cada intento queda guardado
    estado_curso: Optional[str] = None  # APROBADA / REPROBADA si con esta se cerró el curso
    promedio_curso: Optional[float] = None
    mensaje: str
