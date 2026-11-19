"""
PATRONES STRATEGY (comportamiento) + ADAPTER (estructural) - HU-09

Son dos patrones distintos que trabajan juntos en el pago de un curso:

1) ADAPTER: la pasarela de pagos es un sistema EXTERNO que habla "otro idioma"
   (recibe un diccionario raro y responde códigos como "00" o "51").
   El adaptador traduce ese idioma al nuestro (APROBADO / RECHAZADO).
   Si mañana cambiamos de proveedor, solo se cambia el adaptador.
   - Objetivo (lo que nuestro sistema espera) -> PasarelaPago
   - Adaptado (el sistema externo)            -> ProveedorPagosSimulado
   - Adaptador                                -> PasarelaSimuladaAdapter

2) STRATEGY: el estudiante puede pagar con tarjeta o con PSE. Cada medio
   valida y arma la transacción distinto. Cada medio es una "estrategia" y el
   checkout usa la que el estudiante elija, sin ifs por cada medio.
   - Estrategia            -> EstrategiaPago
   - Estrategias concretas -> PagoTarjeta, PagoPSE
   - Contexto              -> ContextoPago (lo usa el checkout, services/checkout.py)

La pasarela es SIMULADA: no se cobra dinero real (así quedó acordado en el MVP).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
import uuid

APROBADO = "APROBADO"
RECHAZADO = "RECHAZADO"


@dataclass
class ResultadoPago:
    """Respuesta ya traducida a nuestro idioma."""

    estado: str  # APROBADO o RECHAZADO
    referencia: str  # código de la transacción que devuelve la pasarela
    mensaje: str

    @property
    def aprobado(self) -> bool:
        return self.estado == APROBADO


# ===========================================================================
# ADAPTER
# ===========================================================================
class ProveedorPagosSimulado:
    """
    ADAPTADO: hace de cuenta que es el SDK de un proveedor externo.
    Su "idioma" no se parece al nuestro: recibe un payload con nombres en inglés
    y responde un código de respuesta bancaria.
    Regla de la simulación: si la tarjeta termina en 0002 o el banco es
    "BANCO_RECHAZO", la transacción se rechaza; en otro caso se aprueba.
    """

    def procesar_transaccion(self, payload: Dict) -> Dict:
        fuente = payload.get("source", {})
        rechazar = fuente.get("card_last4") == "0002" or fuente.get("bank_code") == "BANCO_RECHAZO"
        return {
            "transaction_id": f"PAG-{uuid.uuid4().hex[:8].upper()}",
            "response_code": "51" if rechazar else "00",  # 00 = aprobada, 51 = fondos insuficientes
            "amount_in_cents": payload.get("amount_in_cents"),
        }


class PasarelaPago(ABC):
    """OBJETIVO: lo único que nuestro sistema conoce de una pasarela."""

    @abstractmethod
    def cobrar(self, monto: float, referencia: str, fuente: Dict) -> ResultadoPago:
        """Cobra el monto y devuelve el resultado en nuestro idioma."""


class PasarelaSimuladaAdapter(PasarelaPago):
    """ADAPTADOR: traduce entre nuestro sistema y el proveedor externo."""

    CODIGOS_APROBADOS = {"00"}

    def __init__(self, proveedor: ProveedorPagosSimulado = None):
        self.proveedor = proveedor or ProveedorPagosSimulado()

    def cobrar(self, monto: float, referencia: str, fuente: Dict) -> ResultadoPago:
        # 1. Traducimos nuestros datos al formato del proveedor (pesos -> centavos, nombres en inglés)
        payload = {"amount_in_cents": int(round(monto * 100)), "reference": referencia, "source": fuente}
        # 2. Llamamos al sistema externo
        respuesta = self.proveedor.procesar_transaccion(payload)
        # 3. Traducimos su respuesta a la nuestra
        if respuesta["response_code"] in self.CODIGOS_APROBADOS:
            return ResultadoPago(APROBADO, respuesta["transaction_id"], "Pago aprobado")
        return ResultadoPago(RECHAZADO, respuesta["transaction_id"], "Transacción rechazada. Por favor intente con otro método de pago")


# ===========================================================================
# STRATEGY
# ===========================================================================
class EstrategiaPago(ABC):
    """Contrato común de cualquier medio de pago.

    El cliente (ContextoPago) solo llama a pagar(); validar() y armar_fuente() son los dos pasos
    que pagar() ejecuta en orden y que cada medio de pago concreto define (plantilla de pasos).
    """

    nombre: str = ""

    @abstractmethod
    def validar(self, datos: Dict) -> None:
        """Revisa los datos del medio de pago. Si algo está mal, lanza ValueError."""

    @abstractmethod
    def armar_fuente(self, datos: Dict) -> Dict:
        """Prepara los datos que necesita la pasarela, sin guardar datos sensibles."""

    def pagar(self, pasarela: PasarelaPago, monto: float, referencia: str, datos: Dict) -> ResultadoPago:
        """Paso a paso igual para todos los medios: validar, armar y cobrar."""
        self.validar(datos)
        return pasarela.cobrar(monto, referencia, self.armar_fuente(datos))


class PagoTarjeta(EstrategiaPago):
    nombre = "TARJETA"

    def validar(self, datos: Dict) -> None:
        numero = str(datos.get("numero_tarjeta", "")).replace(" ", "")
        if not (numero.isdigit() and len(numero) == 16):
            raise ValueError("El número de tarjeta debe tener 16 dígitos")
        if not datos.get("titular"):
            raise ValueError("Debe escribir el nombre del titular")

    def armar_fuente(self, datos: Dict) -> Dict:
        numero = str(datos["numero_tarjeta"]).replace(" ", "")
        # Por seguridad solo viajan los últimos 4 dígitos (nunca guardamos el número completo)
        return {"type": "CARD", "card_last4": numero[-4:], "holder": datos["titular"]}


class PagoPSE(EstrategiaPago):
    nombre = "PSE"

    TIPOS_PERSONA = ("NATURAL", "JURIDICA")

    def validar(self, datos: Dict) -> None:
        if not datos.get("banco"):
            raise ValueError("Debe seleccionar un banco")
        if str(datos.get("tipo_persona", "")).upper() not in self.TIPOS_PERSONA:
            raise ValueError("El tipo de persona debe ser NATURAL o JURIDICA")

    def armar_fuente(self, datos: Dict) -> Dict:
        return {"type": "PSE", "bank_code": datos["banco"], "person_type": str(datos["tipo_persona"]).upper()}


# Para agregar otro medio (ej. Nequi) se crea su clase y se agrega aquí, sin tocar el checkout.
ESTRATEGIAS: Dict[str, EstrategiaPago] = {
    PagoTarjeta.nombre: PagoTarjeta(),
    PagoPSE.nombre: PagoPSE(),
}


def obtener_estrategia(metodo: str) -> EstrategiaPago:
    estrategia = ESTRATEGIAS.get((metodo or "").upper())
    if not estrategia:
        raise ValueError(f"Medio de pago no soportado: {metodo}")
    return estrategia


class ContextoPago:
    """
    CONTEXTO del Strategy: guarda el medio de pago que eligió el estudiante y lo usa.
    No sabe si es tarjeta o PSE; solo le dice a la estrategia "paga". La pasarela le
    llega desde afuera (Inversión de Dependencias), así en las pruebas se usa una falsa.
    """

    def __init__(self, estrategia: EstrategiaPago, pasarela: PasarelaPago):
        self.estrategia = estrategia
        self.pasarela = pasarela

    def cambiar_estrategia(self, estrategia: EstrategiaPago) -> None:
        """Si el estudiante cambia de medio de pago, se cambia la estrategia y nada más."""
        self.estrategia = estrategia

    def procesar_pago(self, monto: float, referencia: str, datos: Dict) -> ResultadoPago:
        return self.estrategia.pagar(self.pasarela, monto, referencia, datos)
