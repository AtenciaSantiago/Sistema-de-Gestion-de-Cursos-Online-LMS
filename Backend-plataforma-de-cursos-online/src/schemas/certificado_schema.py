from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

class CertificadoResponse(BaseModel):
    id_certificado: UUID
    id_inscripcion: UUID
    codigo_verificacion: Optional[str] = None
    promedio_final: Optional[float] = None
    nombre_estudiante: Optional[str] = None
    nombre_curso: Optional[str] = None
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
