from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PagoResponse(BaseModel):
    id_pago: UUID
    id_usuario: UUID
    nombre_estudiante: Optional[str] = None
    id_curso: UUID
    nombre_curso: Optional[str] = None
    monto: float
    estado_pago: str
    metodo_pago: str
    referencia: Optional[str] = None
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
