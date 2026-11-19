import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.database.config import Base


class Certificado(Base):
    __tablename__ = "certificado"
    # Entregable 2: un solo certificado por inscripción aprobada
    __table_args__ = (UniqueConstraint("id_inscripcion", name="uq_certificado_inscripcion"),)

    id_certificado = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    id_inscripcion = Column(
        UUID(as_uuid=True), ForeignKey("inscripcion.id_inscripcion"), nullable=False
    )

    # Entregable 2 (HU-13 / RN-04): código único verificable y promedio con el que aprobó
    codigo_verificacion = Column(String(30), nullable=True, unique=True)
    promedio_final = Column(Float, nullable=True)

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

    @property
    def nombre_estudiante(self):
        return self.inscripcion.usuario_inscrito.nombre_usuario if self.inscripcion else None

    @property
    def nombre_curso(self):
        return self.inscripcion.curso.nombre_curso if self.inscripcion else None
