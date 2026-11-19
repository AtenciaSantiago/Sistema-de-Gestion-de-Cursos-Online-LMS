"""
PATRÓN FACTORY METHOD (creacional) - HU-14 y HU-15

¿Qué problema resuelve?
Una evaluación puede tener distintos TIPOS de pregunta (opción múltiple,
verdadero/falso). Cada tipo se arma y se califica distinto. Si metiéramos un
"if tipo == ..." en cada parte del código, cada tipo nuevo obligaría a tocar
todo. Con Factory Method, cada tipo tiene su propio "creador" y el resto del
sistema solo pide "créame la pregunta" sin saber cuál es.

OJO (esto lo pidió la profe): la Factory crea PREGUNTAS, no evaluaciones.
La evaluación es una entidad simple (nombre, porcentaje, nota mínima);
lo que cambia según el tipo son las preguntas que la componen.

Roles del patrón:
- Producto            -> Pregunta (clase abstracta)
- Productos concretos -> PreguntaOpcionMultiple, PreguntaVerdaderoFalso
- Creador             -> CreadorPregunta (tiene el método fábrica crear_pregunta)
- Creadores concretos -> CreadorPreguntaOpcionMultiple, CreadorPreguntaVerdaderoFalso
"""

from abc import ABC, abstractmethod
from typing import Dict, List


# HU-14 esc. 3: mensaje cuando falta la clave (respuesta correcta)
MENSAJE_CLAVE_INVALIDA = "Debe seleccionar la respuesta correcta y definir una nota de aprobación válida"


# ---------------------------------------------------------------------------
# PRODUCTO: lo que todas las preguntas deben saber hacer
# ---------------------------------------------------------------------------
class Pregunta(ABC):
    """Contrato común de cualquier pregunta. El que califica solo conoce esto."""

    def __init__(self, enunciado: str, respuesta_correcta: str):
        self.enunciado = (enunciado or "").strip()
        self.respuesta_correcta = (respuesta_correcta or "").strip()

    @abstractmethod
    def opciones(self) -> List[str]:
        """Las opciones que ve el estudiante."""

    @abstractmethod
    def validar(self) -> None:
        """Revisa que la pregunta esté bien armada. Si no, lanza ValueError."""

    def es_correcta(self, respuesta: str) -> bool:
        """Compara lo que respondió el estudiante con la clave (sin importar mayúsculas)."""
        return (respuesta or "").strip().lower() == self.respuesta_correcta.lower()


# ---------------------------------------------------------------------------
# PRODUCTOS CONCRETOS: un tipo de pregunta por clase
# ---------------------------------------------------------------------------
class PreguntaOpcionMultiple(Pregunta):
    """Pregunta con varias opciones y una sola correcta."""

    def __init__(self, enunciado: str, opciones: List[str], respuesta_correcta: str):
        super().__init__(enunciado, respuesta_correcta)
        self._opciones = [o.strip() for o in (opciones or []) if o and o.strip()]
        # Si el docente escribió la clave con otras mayúsculas, se guarda igual a la opción
        for opcion in self._opciones:
            if self.respuesta_correcta.lower() == opcion.lower():
                self.respuesta_correcta = opcion

    def opciones(self) -> List[str]:
        return list(self._opciones)

    def validar(self) -> None:
        if not self.enunciado:
            raise ValueError("La pregunta debe tener un enunciado")
        if len(self._opciones) < 2:
            raise ValueError("Una pregunta de opción múltiple necesita al menos 2 opciones")
        if len({o.lower() for o in self._opciones}) != len(self._opciones):
            raise ValueError("Las opciones de la pregunta no se pueden repetir")
        if self.respuesta_correcta not in self._opciones:
            raise ValueError(MENSAJE_CLAVE_INVALIDA)


class PreguntaVerdaderoFalso(Pregunta):
    """Pregunta que solo se responde con Verdadero o Falso."""

    OPCIONES = ["Verdadero", "Falso"]

    def __init__(self, enunciado: str, respuesta_correcta: str):
        super().__init__(enunciado, respuesta_correcta)
        # Se acepta "verdadero", "VERDADERO", etc. y se guarda siempre igual
        for opcion in self.OPCIONES:
            if self.respuesta_correcta.lower() == opcion.lower():
                self.respuesta_correcta = opcion

    def opciones(self) -> List[str]:
        return list(self.OPCIONES)

    def validar(self) -> None:
        if not self.enunciado:
            raise ValueError("La pregunta debe tener un enunciado")
        if self.respuesta_correcta not in self.OPCIONES:
            raise ValueError(MENSAJE_CLAVE_INVALIDA)


# ---------------------------------------------------------------------------
# CREADOR: define el método fábrica y el paso a paso común
# ---------------------------------------------------------------------------
class CreadorPregunta(ABC):
    """Cada tipo de pregunta tiene su creador. Todos siguen el mismo paso a paso."""

    @abstractmethod
    def crear_pregunta(self, datos: Dict) -> Pregunta:
        """MÉTODO FÁBRICA: cada creador concreto decide qué clase de pregunta construir."""

    def preparar_pregunta(self, datos: Dict) -> Pregunta:
        """Paso a paso que comparten todos: crear la pregunta y validarla."""
        pregunta = self.crear_pregunta(datos)
        pregunta.validar()
        return pregunta


# ---------------------------------------------------------------------------
# CREADORES CONCRETOS
# ---------------------------------------------------------------------------
class CreadorPreguntaOpcionMultiple(CreadorPregunta):
    def crear_pregunta(self, datos: Dict) -> Pregunta:
        return PreguntaOpcionMultiple(
            enunciado=datos.get("enunciado"),
            opciones=datos.get("opciones") or [],
            respuesta_correcta=datos.get("respuesta_correcta"),
        )


class CreadorPreguntaVerdaderoFalso(CreadorPregunta):
    def crear_pregunta(self, datos: Dict) -> Pregunta:
        return PreguntaVerdaderoFalso(
            enunciado=datos.get("enunciado"),
            respuesta_correcta=datos.get("respuesta_correcta"),
        )


# ---------------------------------------------------------------------------
# Registro de creadores: para agregar un tipo nuevo (ej. "RESPUESTA_CORTA")
# solo se crea su clase y se agrega aquí. No hay que tocar el resto del código.
# ---------------------------------------------------------------------------
CREADORES: Dict[str, CreadorPregunta] = {
    "OPCION_MULTIPLE": CreadorPreguntaOpcionMultiple(),
    "VERDADERO_FALSO": CreadorPreguntaVerdaderoFalso(),
}


def obtener_creador(tipo: str) -> CreadorPregunta:
    """Devuelve el creador según el tipo que mande el docente."""
    creador = CREADORES.get((tipo or "").upper())
    if not creador:
        raise ValueError(f"Tipo de pregunta no soportado: {tipo}")
    return creador
