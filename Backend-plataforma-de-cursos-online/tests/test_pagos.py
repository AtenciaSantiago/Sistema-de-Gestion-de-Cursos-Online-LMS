"""
Pruebas de Strategy + Adapter (pago del curso, HU-09) y del catálogo (HU-06).
"""

import pytest

from conftest import crear_usuario, token_de
from src.endpoints.checkout import obtener_pasarela
from src.app import app
from src.entities.Curso import Curso
from src.patrones.pagos import (
    APROBADO,
    RECHAZADO,
    EstrategiaPago,
    PagoPSE,
    PagoTarjeta,
    PasarelaPago,
    PasarelaSimuladaAdapter,
    ProveedorPagosSimulado,
    ResultadoPago,
    obtener_estrategia,
)

TARJETA_OK = {"numero_tarjeta": "4242 4242 4242 4242", "titular": "Lucía Martínez"}
TARJETA_RECHAZADA = {"numero_tarjeta": "4000 0000 0000 0002", "titular": "Lucía Martínez"}
PSE_OK = {"banco": "BANCOLOMBIA", "tipo_persona": "NATURAL"}

DATOS_POR_METODO = {"TARJETA": TARJETA_OK, "PSE": PSE_OK}


class PasarelaFalsa(PasarelaPago):
    """Pasarela de mentiras para probar sin el proveedor (así se ve la Inversión de Dependencias)."""

    def __init__(self, estado=APROBADO):
        self.estado = estado
        self.llamadas = []

    def cobrar(self, monto, referencia, fuente):
        self.llamadas.append({"monto": monto, "referencia": referencia, "fuente": fuente})
        return ResultadoPago(self.estado, "PAG-FALSO", "respuesta falsa")


# ---------------------------- ADAPTER --------------------------------------
def test_adapter_traduce_codigo_00_a_aprobado():
    r = PasarelaSimuladaAdapter().cobrar(120.0, "INS-1", {"type": "CARD", "card_last4": "4242"})
    assert r.estado == APROBADO and r.referencia.startswith("PAG-")


def test_adapter_traduce_codigo_51_a_rechazado():
    r = PasarelaSimuladaAdapter().cobrar(120.0, "INS-1", {"type": "CARD", "card_last4": "0002"})
    assert r.estado == RECHAZADO


def test_adapter_convierte_pesos_a_centavos_para_el_proveedor():
    class ProveedorEspia(ProveedorPagosSimulado):
        def procesar_transaccion(self, payload):
            self.payload = payload
            return super().procesar_transaccion(payload)

    espia = ProveedorEspia()
    PasarelaSimuladaAdapter(espia).cobrar(120.5, "INS-1", {"type": "PSE", "bank_code": "X"})
    assert espia.payload["amount_in_cents"] == 12050


# ---------------------------- STRATEGY -------------------------------------
def test_cada_medio_tiene_su_estrategia():
    assert isinstance(obtener_estrategia("tarjeta"), PagoTarjeta)
    assert isinstance(obtener_estrategia("PSE"), PagoPSE)
    with pytest.raises(ValueError):
        obtener_estrategia("BITCOIN")


def test_tarjeta_no_envia_el_numero_completo():
    fuente = PagoTarjeta().armar_fuente(TARJETA_OK)
    assert fuente["card_last4"] == "4242"
    assert "4242424242424242" not in str(fuente)


def test_datos_invalidos_se_rechazan_antes_de_cobrar():
    pasarela = PasarelaFalsa()
    with pytest.raises(ValueError):
        PagoTarjeta().pagar(pasarela, 120.0, "INS-1", {"numero_tarjeta": "123", "titular": "x"})
    with pytest.raises(ValueError):
        PagoPSE().pagar(pasarela, 120.0, "INS-1", {"banco": "", "tipo_persona": "NATURAL"})
    assert pasarela.llamadas == []  # nunca se llegó a cobrar


@pytest.mark.parametrize("metodo", list(DATOS_POR_METODO))
def test_sustitucion_lsp_cualquier_estrategia_paga_igual(metodo):
    """
    LSP: el checkout solo conoce EstrategiaPago. Cualquier medio puede
    reemplazarla: valida, llama UNA vez a la pasarela con el monto y la
    referencia, y devuelve un ResultadoPago.
    """
    estrategia = obtener_estrategia(metodo)
    pasarela = PasarelaFalsa()
    resultado = estrategia.pagar(pasarela, 120.0, "INS-ABC", DATOS_POR_METODO[metodo])

    assert isinstance(estrategia, EstrategiaPago)
    assert isinstance(resultado, ResultadoPago)
    assert len(pasarela.llamadas) == 1
    assert pasarela.llamadas[0]["monto"] == 120.0
    assert pasarela.llamadas[0]["referencia"] == "INS-ABC"


# ---------------------------- API ------------------------------------------
@pytest.fixture()
def estudiante_nuevo(db):
    return crear_usuario(db, "Carlos Ruiz", "carlos@email.com", "400", "Estudiante")


def test_catalogo_solo_muestra_cursos_publicados(cliente, escenario, db):
    db.add(Curso(
        id_categoria=escenario["categoria"].id_categoria, nombre_curso="Curso en borrador",
        duracion_horas=5, estado_curso="BORRADOR", precio=50, id_usuario_creacion=escenario["docente"].id_usuario,
    ))
    db.commit()
    nombres = [c["nombre_curso"] for c in cliente.get("/catalogo").json()]
    assert nombres == ["Diseño de interfaces con Figma"]


@pytest.mark.parametrize("metodo", list(DATOS_POR_METODO))
def test_pago_aprobado_activa_la_inscripcion_sola(cliente, escenario, estudiante_nuevo, metodo):
    r = cliente.post(
        f"/checkout/cursos/{escenario['curso'].id_curso}",
        headers=token_de(estudiante_nuevo),
        json={"metodo_pago": metodo, **DATOS_POR_METODO[metodo]},
    )
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["aprobado"] is True
    assert cuerpo["estado_inscripcion"] == "ACTIVA"
    assert cuerpo["monto"] == 120.0
    assert cuerpo["metodo_pago"] == metodo


def test_pago_rechazado_deja_la_inscripcion_pendiente(cliente, escenario, estudiante_nuevo):
    r = cliente.post(
        f"/checkout/cursos/{escenario['curso'].id_curso}",
        headers=token_de(estudiante_nuevo),
        json={"metodo_pago": "TARJETA", **TARJETA_RECHAZADA},
    )
    assert r.json()["aprobado"] is False
    assert r.json()["estado_inscripcion"] == "PENDIENTE"


def test_no_se_cobra_dos_veces_si_ya_esta_matriculado(cliente, escenario):
    r = cliente.post(
        f"/checkout/cursos/{escenario['curso'].id_curso}",
        headers=token_de(escenario["estudiante"]),  # Lucía ya tiene inscripción ACTIVA
        json={"metodo_pago": "TARJETA", **TARJETA_OK},
    )
    assert r.status_code == 400
    assert "Ya te encuentras matriculado" in r.json()["detail"]


def test_la_pasarela_se_puede_cambiar_sin_tocar_el_checkout(cliente, escenario, estudiante_nuevo):
    """DIP: reemplazamos la pasarela real por una falsa desde afuera."""
    falsa = PasarelaFalsa(estado=RECHAZADO)
    app.dependency_overrides[obtener_pasarela] = lambda: falsa
    try:
        r = cliente.post(
            f"/checkout/cursos/{escenario['curso'].id_curso}",
            headers=token_de(estudiante_nuevo),
            json={"metodo_pago": "TARJETA", **TARJETA_OK},
        )
    finally:
        app.dependency_overrides.clear()
    assert r.json()["aprobado"] is False
    assert len(falsa.llamadas) == 1


def test_el_contexto_puede_cambiar_de_estrategia_sin_cambiar_nada_mas():
    """STRATEGY: el contexto no sabe qué medio usa; se le cambia la estrategia y sigue igual."""
    from src.patrones.pagos import ContextoPago
    pasarela = PasarelaFalsa()
    contexto = ContextoPago(PagoTarjeta(), pasarela)
    contexto.procesar_pago(120.0, "INS-1", TARJETA_OK)
    contexto.cambiar_estrategia(PagoPSE())
    contexto.procesar_pago(120.0, "INS-1", {"banco": "BANCOLOMBIA", "tipo_persona": "natural"})
    assert [l["fuente"]["type"] for l in pasarela.llamadas] == ["CARD", "PSE"]
