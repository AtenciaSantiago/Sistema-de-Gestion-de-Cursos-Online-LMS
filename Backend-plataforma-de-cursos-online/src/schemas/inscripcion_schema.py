from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.entities.inscripcion import EstadoInscripcion
from src.schemas.base_schema import EntradaSchema


class InscripcionCreate(EntradaSchema):
    """RF-10: matrícula manual que hace el Admin (por ejemplo, una beca). Queda ACTIVA."""

    id_curso: UUID
    id_usuario_inscrito: UUID


class InscripcionResponse(BaseModel):
    id_inscripcion: UUID
    id_curso: UUID
    nombre_curso: Optional[str] = None
    id_usuario_inscrito: UUID
    nombre_estudiante: Optional[str] = None
    estado_inscripcion: EstadoInscripcion
    # Para la auditoría de cierres (RF-18 / HU-17): promedio final y código del certificado
    promedio_final: Optional[float] = None
    codigo_certificado: Optional[str] = None
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
