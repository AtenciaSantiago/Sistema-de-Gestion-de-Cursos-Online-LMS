import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base


class IntentoEvaluacion(Base):
    """
    Cada vez que el estudiante presenta una evaluación queda un intento (RF-13, HU-15 esc. 2).
    La tabla Calificacion guarda la nota vigente; aquí queda el historial completo
    para que nadie pueda decir "yo había sacado más" (trazabilidad).
    """

    __tablename__ = "intento_evaluacion"

    id_intento = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_inscripcion = Column(UUID(as_uuid=True), ForeignKey("inscripcion.id_inscripcion"), nullable=False, index=True)
    id_evaluacion = Column(UUID(as_uuid=True), ForeignKey("evaluacion.id_evaluacion"), nullable=False, index=True)
    numero_intento = Column(Integer, nullable=False)
    correctas = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    nota = Column(Float, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

    inscripcion = relationship("Inscripcion", foreign_keys=[id_inscripcion])
    evaluacion = relationship("Evaluacion", foreign_keys=[id_evaluacion])
