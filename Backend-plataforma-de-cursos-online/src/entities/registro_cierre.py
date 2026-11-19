import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from src.database.config import Base


class RegistroCierre(Base):
    """
    Bitácora de auditoría de cada cierre académico (RF-18 / base para HU-17).
    La llena el ObservadorAuditoria cada vez que el sistema cierra un curso.
    """

    __tablename__ = "registro_cierre"

    id_registro = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_inscripcion = Column(UUID(as_uuid=True), ForeignKey("inscripcion.id_inscripcion"), nullable=False, index=True)
    estado_final = Column(String(20), nullable=False)  # APROBADA o REPROBADA
    promedio = Column(Float, nullable=False)
    detalle = Column(String(255), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
