import uuid

from sqlalchemy import Column, ForeignKey, String, Text, Integer, DateTime, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.config import Base


class Leccion(Base):
    """Modelo de lección"""

    __tablename__ = "leccion"
    # Entregable 2: el orden es único DENTRO de cada curso (antes era único en toda la base,
    # y por eso dos cursos no podían tener cada uno su "lección 1").
    __table_args__ = (UniqueConstraint("id_curso", "orden", name="uq_leccion_curso_orden"),)

    id_leccion = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    
    id_curso = Column(
        UUID(as_uuid=True), ForeignKey("curso.id_curso"), nullable=False
    
    )

    titulo_leccion = Column(String(150), nullable=False)  # Entregable 2: antes 20 caracteres
    descripcion_leccion = Column(Text, nullable=True)
    orden = Column(Integer, nullable=False)
    duracion_horas = Column(Integer, nullable=False)
 
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
    curso = relationship("Curso", foreign_keys=[id_curso])