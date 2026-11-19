"""
Checkout: el estudiante paga un curso y queda matriculado solo (HU-09).

Aquí se usa el patrón Strategy: se arma un ContextoPago con el medio de pago que
eligió el estudiante y el contexto le pide a esa estrategia que pague. No hay
ifs por cada medio de pago.

La pasarela llega "inyectada" desde afuera (principio de Inversión de
Dependencias): este servicio solo conoce la clase abstracta PasarelaPago,
no al proveedor externo. En las pruebas se le pasa una pasarela falsa.
"""

from dataclasses import dataclass
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.Curso import Curso
from src.entities.Pago import Pago
from src.entities.inscripcion import EstadoInscripcion, Inscripcion
from src.patrones.pagos import ContextoPago, PasarelaPago, ResultadoPago, obtener_estrategia
from src.services.curso import esta_publicado

MENSAJE_YA_MATRICULADO = "Ya te encuentras matriculado activamente en este curso"  # HU-09 esc. 3
MENSAJE_YA_FINALIZADO = "Ya finalizaste este curso; no se puede volver a comprar"


@dataclass
class ResultadoCheckout:
    resultado: ResultadoPago
    pago: Pago
    inscripcion: Inscripcion


def pagar_curso(
    db: Session,
    id_estudiante: UUID,
    id_curso: UUID,
    metodo: str,
    datos_pago: Dict,
    pasarela: PasarelaPago,
) -> ResultadoCheckout:
    curso = db.query(Curso).filter(Curso.id_curso == id_curso).first()
    if not esta_publicado(curso):
        raise ValueError("El curso no existe o no está publicado")

    # HU-09 escenario 3: si ya está matriculado, no se cobra otra vez
    inscripcion = (
        db.query(Inscripcion)
        .filter(Inscripcion.id_usuario_inscrito == id_estudiante, Inscripcion.id_curso == id_curso)
        .first()
    )
    if inscripcion and inscripcion.estado_inscripcion == EstadoInscripcion.ACTIVA.value:
        raise ValueError(MENSAJE_YA_MATRICULADO)
    if inscripcion and inscripcion.estado_inscripcion in (EstadoInscripcion.APROBADA.value, EstadoInscripcion.REPROBADA.value):
        raise ValueError(MENSAJE_YA_FINALIZADO)  # no se cobra otra vez ni se borra su resultado

    # Si no tenía inscripción, se crea en PENDIENTE mientras se procesa el pago
    if not inscripcion:
        inscripcion = Inscripcion(
            id_curso=id_curso,
            id_usuario_inscrito=id_estudiante,
            estado_inscripcion=EstadoInscripcion.PENDIENTE.value,
            id_usuario_creacion=id_estudiante,
        )
        db.add(inscripcion)
        db.flush()

    # STRATEGY: el contexto recibe la estrategia del medio que eligió el estudiante
    estrategia = obtener_estrategia(metodo)
    contexto = ContextoPago(estrategia, pasarela)
    resultado = contexto.procesar_pago(
        monto=curso.precio or 0.0,
        referencia=f"INS-{str(inscripcion.id_inscripcion)[:8].upper()}",
        datos=datos_pago,
    )

    # Siempre queda registro del pago (aprobado o rechazado) para la auditoría
    pago = Pago(
        id_usuario=id_estudiante,
        id_curso=id_curso,
        monto=curso.precio or 0.0,
        estado_pago=resultado.estado,
        metodo_pago=estrategia.nombre,
        referencia=resultado.referencia,
        id_usuario_creacion=id_estudiante,
    )
    db.add(pago)

    # RN-01: solo con pago APROBADO la inscripción pasa a ACTIVA (sin intervención del admin)
    if resultado.aprobado:
        inscripcion.estado_inscripcion = EstadoInscripcion.ACTIVA.value
        inscripcion.id_usuario_edita = id_estudiante

    db.commit()
    db.refresh(pago)
    db.refresh(inscripcion)
    return ResultadoCheckout(resultado=resultado, pago=pago, inscripcion=inscripcion)

