from sqlalchemy import Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.config import Base


class Calificacion(Base):
    __tablename__ = "calificacion"

    id_inscripcion = Column(UUID(as_uuid=True), ForeignKey("inscripcion.id_inscripcion"), primary_key=True)
    id_evaluacion = Column(UUID(as_uuid=True), ForeignKey("evaluacion.id_evaluacion"), primary_key=True)

    Nota = Column(Float, nullable=False)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_edicion = Column(DateTime(timezone=True), onupdate=func.now())
    id_usuario_creacion = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_usuario_edita = Column(
        UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=True
    )

    usuario_creacion = relationship("Usuario", foreign_keys=[id_usuario_creacion])
    usuario_edita = relationship("Usuario", foreign_keys=[id_usuario_edita])
    inscripcion = relationship("Inscripcion", foreign_keys=[id_inscripcion])
    evaluacion = relationship("Evaluacion", foreign_keys=[id_evaluacion])

    # Nombres para mostrar en la tabla del Admin / Docente
    @property
    def nombre_evaluacion(self):
        return self.evaluacion.nombre_evaluacion if self.evaluacion else None

    @property
    def nombre_estudiante(self):
        return self.inscripcion.usuario_inscrito.nombre_usuario if self.inscripcion else None

    @property
    def nombre_curso(self):
        return self.inscripcion.curso.nombre_curso if self.inscripcion else None
