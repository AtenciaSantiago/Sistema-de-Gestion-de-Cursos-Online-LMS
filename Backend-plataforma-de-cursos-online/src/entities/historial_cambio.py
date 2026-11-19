import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base


class HistorialCambio(Base):
    """
    RF-07 Control de cambios (problema P7 del modelo verbal): registro de usuario, fecha y detalle
    de cada modificación o eliminación de un contenido activo (curso, lección, material,
    evaluación, pregunta o categoría). Lo consulta el Administrador (GET /historial).
    Las calificaciones no se editan a mano (las calcula el sistema, RF-13), por eso no aparecen aquí.
    """

    __tablename__ = "historial_cambio"

    id_historial = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    entidad = Column(String(20), nullable=False, index=True)  # CURSO, LECCION, MATERIAL, EVALUACION, PREGUNTA, CATEGORIA
    id_registro = Column(UUID(as_uuid=True), nullable=False, index=True)  # id del contenido modificado
    nombre_registro = Column(String(255), nullable=True)  # cómo se llamaba (sirve aunque ya se haya eliminado)
    accion = Column(String(15), nullable=False)  # ACTUALIZAR o ELIMINAR
    detalle = Column(Text, nullable=False)  # qué cambió: campo: antes -> después
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    usuario = relationship("Usuario", foreign_keys=[id_usuario])
