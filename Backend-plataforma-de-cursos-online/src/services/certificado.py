"""
Certificados (HU-13, RF-16, RN-04).

Regla única para emitir un certificado: la aplica el cierre académico automático
(ObservadorCertificado, HU-16) y nadie más: solo con inscripción APROBADA
y siempre con un código de verificación único. No hay emisión manual.
"""

from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.certificado import Certificado
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.entities.usuario import Usuario
from src.patrones.certificado_generador import (
    DatosCertificado,
    DocumentoCertificado,
    GeneradorCertificado,
    GeneradorCertificadoPDF,
)

MENSAJE_NO_DISPONIBLE = "El certificado estará disponible una vez el curso sea aprobado"  # HU-13 esc. 2
MENSAJE_NO_CUMPLE = "No cumple con las condiciones para la emisión del certificado"  # HU-13 esc. 3


def _generar_codigo() -> str:
    return f"CERT-{datetime.now().year}-{uuid4().hex[:6].upper()}"


def emitir(db: Session, id_inscripcion: UUID, promedio: Optional[float], id_usuario_creacion: UUID, guardar: bool = True) -> Certificado:
    """Emite el certificado si la inscripción está APROBADA. Si ya existe, devuelve el mismo."""
    inscripcion = db.query(Inscripcion).filter(Inscripcion.id_inscripcion == id_inscripcion).first()
    if not inscripcion or inscripcion.estado_inscripcion != EstadoInscripcion.APROBADA.value:
        raise ValueError(MENSAJE_NO_CUMPLE)  # RN-04

    existente = db.query(Certificado).filter(Certificado.id_inscripcion == id_inscripcion).first()
    if existente:
        return existente

    certificado = Certificado(
        id_inscripcion=id_inscripcion,
        codigo_verificacion=_generar_codigo(),
        promedio_final=promedio,
        id_usuario_creacion=id_usuario_creacion,
    )
    db.add(certificado)
    if guardar:
        db.commit()
        db.refresh(certificado)
    return certificado


def generar_documento(
    db: Session, id_estudiante: UUID, id_curso: UUID, generador: Optional[GeneradorCertificado] = None
) -> Tuple[DocumentoCertificado, str]:
    """
    HU-13: arma el certificado del estudiante con el patrón Template Method.
    Devuelve (documento, codigo). Por defecto el documento es un PDF.
    """
    inscripcion = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == id_estudiante, Inscripcion.id_curso == id_curso)
        .first()
    )
    if not inscripcion:
        raise PermissionError("No cuenta con una inscripción en este curso")
    if inscripcion.estado_inscripcion in (EstadoInscripcion.PENDIENTE.value, EstadoInscripcion.ACTIVA.value):
        raise PermissionError(MENSAJE_NO_DISPONIBLE)
    if inscripcion.estado_inscripcion != EstadoInscripcion.APROBADA.value:
        raise PermissionError(MENSAJE_NO_CUMPLE)  # CANCELADA o REPROBADA
    certificado = db.query(Certificado).filter(Certificado.id_inscripcion == inscripcion.id_inscripcion).first()
    if not certificado:
        raise PermissionError(MENSAJE_NO_DISPONIBLE)

    curso = db.query(Curso).filter(Curso.id_curso == id_curso).first()
    estudiante = db.query(Usuario).filter(Usuario.id_usuario == id_estudiante).first()

    datos = DatosCertificado(
        institucion="Campus Digital",
        estudiante=estudiante.nombre_usuario,
        documento=f"{estudiante.tipo_documento} {estudiante.documento_identidad}",
        curso=curso.nombre_curso,
        horas=curso.duracion_horas,
        docente=curso.nombre_docente or "",  # el profesor ASIGNADO, no quien creó el curso
        fecha=certificado.fecha_creacion.date() if certificado.fecha_creacion else date.today(),
        promedio=certificado.promedio_final or 0.0,
        codigo=certificado.codigo_verificacion,
    )
    # TEMPLATE METHOD: la clase base fija el orden y el generador concreto el formato (PDF por defecto)
    documento = (generador or GeneradorCertificadoPDF()).generar(datos)
    return documento, certificado.codigo_verificacion


def obtener_por_id(db: Session, id_certificado: UUID) -> Optional[Certificado]:
    return db.query(Certificado).filter(Certificado.id_certificado == id_certificado).first()


def obtener_todos(db: Session, skip: int = 0, limit: int = 100) -> List[Certificado]:
    return db.query(Certificado).order_by(Certificado.fecha_creacion.desc()).offset(skip).limit(limit).all()


def verificar(db: Session, codigo: str) -> Optional[dict]:
    """RF-17: cualquiera puede comprobar si un certificado es auténtico con su código."""
    certificado = db.query(Certificado).filter(Certificado.codigo_verificacion == (codigo or "").strip().upper()).first()
    if not certificado:
        return None
    inscripcion = certificado.inscripcion
    return {
        "valido": True,
        "codigo": certificado.codigo_verificacion,
        "estudiante": inscripcion.usuario_inscrito.nombre_usuario,
        "curso": inscripcion.curso.nombre_curso,
        "promedio_final": certificado.promedio_final,
        "fecha_emision": certificado.fecha_creacion,
    }


# Entregable 2: ya no hay "actualizar" ni "eliminar". Un certificado emitido es
# inalterable (RU-04); si se pudiera editar, se podría pasar a nombre de otra persona.
