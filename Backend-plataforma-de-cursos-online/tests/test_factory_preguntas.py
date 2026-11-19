"""
Pruebas del patrón Factory Method (preguntas).

Incluye la PRUEBA DE SUSTITUCIÓN (principio LSP) que pidió la profe:
la misma prueba se corre con cada tipo de pregunta y todas deben comportarse
igual frente al que califica, sin que él sepa cuál tipo es.
"""

import pytest

from src.patrones.factory_preguntas import (
    CreadorPreguntaOpcionMultiple,
    CreadorPreguntaVerdaderoFalso,
    Pregunta,
    PreguntaOpcionMultiple,
    PreguntaVerdaderoFalso,
    obtener_creador,
)

DATOS_VALIDOS = {
    "OPCION_MULTIPLE": {
        "enunciado": "¿Qué principio ordena la mirada?",
        "opciones": ["Jerarquía visual", "Color aleatorio", "Texto pequeño"],
        "respuesta_correcta": "Jerarquía visual",
        "respuesta_incorrecta": "Color aleatorio",
    },
    "VERDADERO_FALSO": {
        "enunciado": "El contraste ayuda a destacar la acción principal.",
        "respuesta_correcta": "Verdadero",
        "respuesta_incorrecta": "Falso",
    },
}


def test_cada_creador_fabrica_su_tipo_de_pregunta():
    om = CreadorPreguntaOpcionMultiple().preparar_pregunta(DATOS_VALIDOS["OPCION_MULTIPLE"])
    vf = CreadorPreguntaVerdaderoFalso().preparar_pregunta(DATOS_VALIDOS["VERDADERO_FALSO"])
    assert isinstance(om, PreguntaOpcionMultiple)
    assert isinstance(vf, PreguntaVerdaderoFalso)


def test_tipo_desconocido_se_rechaza():
    with pytest.raises(ValueError):
        obtener_creador("RESPUESTA_ABIERTA")


def test_opcion_multiple_sin_clave_valida_se_rechaza():
    datos = dict(DATOS_VALIDOS["OPCION_MULTIPLE"], respuesta_correcta="No está en las opciones")
    with pytest.raises(ValueError):
        obtener_creador("OPCION_MULTIPLE").preparar_pregunta(datos)


def test_verdadero_falso_con_clave_invalida_se_rechaza():
    datos = dict(DATOS_VALIDOS["VERDADERO_FALSO"], respuesta_correcta="Tal vez")
    with pytest.raises(ValueError):
        obtener_creador("VERDADERO_FALSO").preparar_pregunta(datos)


@pytest.mark.parametrize("tipo", list(DATOS_VALIDOS))
def test_sustitucion_lsp_todas_las_preguntas_se_califican_igual(tipo):
    """
    LSP: quien califica solo conoce la clase base Pregunta.
    Cualquier subtipo debe poder reemplazarla sin romper nada:
    - es una Pregunta
    - tiene opciones y la clave está entre ellas
    - es_correcta() da True con la clave y False con otra respuesta
    """
    datos = DATOS_VALIDOS[tipo]
    pregunta = obtener_creador(tipo).preparar_pregunta(datos)

    assert isinstance(pregunta, Pregunta)
    assert pregunta.respuesta_correcta in pregunta.opciones()
    assert pregunta.es_correcta(datos["respuesta_correcta"]) is True
    assert pregunta.es_correcta(datos["respuesta_incorrecta"]) is False
    assert pregunta.es_correcta(datos["respuesta_correcta"].upper()) is True  # sin importar mayúsculas
