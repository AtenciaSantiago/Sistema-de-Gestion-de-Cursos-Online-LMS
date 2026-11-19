"""
PATRÓN OBSERVER (comportamiento) - HU-16 cierre académico automático

¿Qué problema resuelve?
Cuando el sistema cierra un curso (APROBADA o REPROBADA), varias partes
tienen que reaccionar: guardar la auditoría, emitir el certificado, y a futuro
quizás mandar un correo. Si el servicio de cierre llamara a cada una
directamente, quedaría amarrado a todas y cada reacción nueva obligaría a
modificarlo. Con Observer, el cierre solo "avisa" y cada interesado reacciona.

Roles del patrón:
- Sujeto (publicador)     -> PublicadorCierre
- Observador (contrato)   -> ObservadorCierre
- Observadores concretos  -> ObservadorAuditoria, ObservadorCertificado
- Evento                  -> EventoCierre (la información que se avisa)

Detalles de diseño:
- El evento solo lleva DATOS del cierre (no la base de datos).
- Cada observador recibe la sesión de base de datos al crearse; el de certificados recibe
  además la función que emite (inversión de dependencias: depende de un contrato, no del
  módulo concreto de certificados).
- Los observadores NO guardan (no hacen commit): el servicio de cierre guarda
  todo junto al final, así el cierre queda completo o no queda nada.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List
import uuid

from sqlalchemy.orm import Session

from src.entities.registro_cierre import RegistroCierre

# DIP: el observador no importa el servicio concreto de certificados; recibe la función de emisión
# al crearse (la inyecta publicador_por_defecto en services/cierre.py). Firma: (db, id_inscripcion,
# promedio, id_usuario_creacion, guardar) -> certificado.
EmisorCertificado = Callable[..., object]

APROBADA = "APROBADA"
REPROBADA = "REPROBADA"


@dataclass(frozen=True)
class EventoCierre:
    """Lo que el publicador le cuenta a los observadores."""

    id_inscripcion: uuid.UUID
    id_estudiante: uuid.UUID
    estado_final: str
    promedio: float


class ObservadorCierre(ABC):
    """Contrato: todo el que quiera enterarse del cierre debe tener este método."""

    @abstractmethod
    def actualizar(self, evento: EventoCierre) -> None:
        """Reacciona al cierre académico."""


class PublicadorCierre:
    """SUJETO: guarda la lista de interesados y les avisa a todos."""

    def __init__(self):
        self._observadores: List[ObservadorCierre] = []

    def suscribir(self, observador: ObservadorCierre) -> None:
        self._observadores.append(observador)

    def desuscribir(self, observador: ObservadorCierre) -> None:
        self._observadores.remove(observador)

    def notificar(self, evento: EventoCierre) -> None:
        for observador in self._observadores:
            observador.actualizar(evento)


class ObservadorAuditoria(ObservadorCierre):
    """Deja registro de TODO cierre (aprobado o reprobado) para la auditoría."""

    def __init__(self, db: Session):
        self.db = db

    def actualizar(self, evento: EventoCierre) -> None:
        self.db.add(
            RegistroCierre(
                id_inscripcion=evento.id_inscripcion,
                estado_final=evento.estado_final,
                promedio=evento.promedio,
                detalle="Cierre automático al presentar la última evaluación",
            )
        )


class ObservadorCertificado(ObservadorCierre):
    """Si el curso quedó APROBADO, emite el certificado con su código único (RN-04)."""

    def __init__(self, db: Session, emitir: EmisorCertificado):
        self.db = db
        self._emitir = emitir  # abstracción inyectada (DIP), no el servicio concreto

    def actualizar(self, evento: EventoCierre) -> None:
        if evento.estado_final != APROBADA:
            return  # reprobado: no hay certificado
        self._emitir(
            self.db,
            id_inscripcion=evento.id_inscripcion,
            promedio=evento.promedio,
            id_usuario_creacion=evento.id_estudiante,
            guardar=False,  # el servicio de cierre guarda todo junto
        )
