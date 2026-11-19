import uuid

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base


class ProgresoLeccion(Base):
    """
    Lecciones que el estudiante marcó como completadas (HU-12).
    Con esto se calcula el % de avance del curso.
    """

    __tablename__ = "progreso_leccion"
    __table_args__ = (UniqueConstraint("id_inscripcion", "id_leccion", name="uq_progreso_inscripcion_leccion"),)

    id_progreso = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_inscripcion = Column(UUID(as_uuid=True), ForeignKey("inscripcion.id_inscripcion"), nullable=False, index=True)
    id_leccion = Column(UUID(as_uuid=True), ForeignKey("leccion.id_leccion"), nullable=False)
    fecha_completada = Column(DateTime(timezone=True), server_default=func.now())

    inscripcion = relationship("Inscripcion", foreign_keys=[id_inscripcion])
    leccion = relationship("Leccion", foreign_keys=[id_leccion])
