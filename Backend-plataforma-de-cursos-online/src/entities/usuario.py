"""
Entidad Usuario (tabla usuario): base de la trazabilidad.
Las demás tablas guardan quién creó y quién editó cada registro
(id_usuario_creacion / id_usuario_edita).
Los esquemas de entrada y salida de la API están en src/schemas/usuario_schema.py.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.database.config import Base

class Usuario(Base):
    """Usuario del sistema (Admin, Docente o Estudiante). Es quien crea/edita registros (trazabilidad)."""

    __tablename__ = "usuario"

    id_usuario = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    nombre_usuario = Column(String(150), nullable=False)
    tipo_documento = Column(String(50), nullable=False)
    documento_identidad = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    contrasena = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True)
    rol = Column(String(50), nullable=False)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
