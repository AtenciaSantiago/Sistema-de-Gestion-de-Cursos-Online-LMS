from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HistorialCambioResponse(BaseModel):
    """RF-07: usuario, fecha y detalle de cada modificación de contenidos activos."""

    id_historial: UUID
    entidad: str
    id_registro: UUID
    nombre_registro: Optional[str] = None
    accion: str
    detalle: str
    id_usuario: UUID
    nombre_usuario: Optional[str] = None
    rol_usuario: Optional[str] = None
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)
