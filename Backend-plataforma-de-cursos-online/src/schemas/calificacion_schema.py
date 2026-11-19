from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalificacionResponse(BaseModel):
    id_inscripcion: UUID
    id_evaluacion: UUID
    nombre_evaluacion: Optional[str] = None
    nombre_estudiante: Optional[str] = None
    nombre_curso: Optional[str] = None
    Nota: float
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
