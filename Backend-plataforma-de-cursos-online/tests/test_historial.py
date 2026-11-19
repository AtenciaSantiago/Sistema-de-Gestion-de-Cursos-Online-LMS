"""
RF-07 Control de cambios (problema P7 del modelo verbal): cada modificación o eliminación de un
contenido activo deja usuario, fecha y detalle; solo el Administrador consulta el historial.
"""

from datetime import timedelta

from conftest import token_de
from src.entities.historial_cambio import HistorialCambio
from src.utils.fechas import hoy_en_colombia


def _historial(cliente, escenario, **filtros):
    r = cliente.get("/historial", headers=token_de(escenario["admin"]), params=filtros)
    assert r.status_code == 200, r.text
    return r.json()


def test_editar_un_curso_deja_usuario_fecha_y_detalle(cliente, db, escenario):
    curso = escenario["curso"]
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["docente"]),
                    json={"duracion_horas": 16, "descripcion_curso": "Versión ampliada"})
    assert r.status_code == 200
    registros = _historial(cliente, escenario)
    assert len(registros) == 1
    reg = registros[0]
    assert reg["entidad"] == "CURSO" and reg["accion"] == "ACTUALIZAR"
    assert reg["nombre_registro"] == "Diseño de interfaces con Figma"
    assert reg["nombre_usuario"] == "Ana Torres" and reg["rol_usuario"] == "Docente"
    assert "duracion_horas: 12 -> 16" in reg["detalle"]
    assert "descripcion_curso: De tu primera idea a un prototipo -> Versión ampliada" in reg["detalle"]
    assert reg["fecha"]


def test_sin_cambios_reales_no_se_registra_nada(cliente, escenario):
    curso = escenario["curso"]
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["docente"]), json={"duracion_horas": 12})
    assert r.status_code == 200
    assert _historial(cliente, escenario) == []


def test_eliminar_un_material_queda_en_el_historial_con_su_nombre(cliente, db, escenario):
    creado = cliente.post("/material", headers=token_de(escenario["docente"]), json={
        "id_leccion": str(escenario["leccion"].id_leccion), "titulo_material": "Guía de color",
        "tipo_material": "PDF", "URL_archivo": "https://campus.co/guia.pdf",
    })
    assert creado.status_code == 201, creado.text
    r = cliente.delete(f"/material/{creado.json()['id_material']}", headers=token_de(escenario["docente"]))
    assert r.status_code == 200
    registros = _historial(cliente, escenario, entidad="MATERIAL")
    assert len(registros) == 1
    assert registros[0]["accion"] == "ELIMINAR"
    assert registros[0]["nombre_registro"] == "Guía de color"
    assert "Material eliminado: Guía de color (PDF)" == registros[0]["detalle"]
    # el registro sobrevive aunque el material ya no exista
    assert db.query(HistorialCambio).count() == 1


def test_publicar_u_ocultar_un_curso_tambien_se_registra(cliente, escenario):
    curso = escenario["curso"]
    r = cliente.put(f"/cursos/{curso.id_curso}", headers=token_de(escenario["admin"]), json={"estado_curso": "BORRADOR"})
    assert r.status_code == 200
    registros = _historial(cliente, escenario, entidad="CURSO")
    assert len(registros) == 1 and "estado_curso: PUBLICADO -> BORRADOR" in registros[0]["detalle"]
    assert registros[0]["nombre_usuario"] == "admin"


def test_el_historial_lo_consulta_solo_el_administrador(cliente, escenario):
    assert cliente.get("/historial", headers=token_de(escenario["docente"])).status_code == 403
    assert cliente.get("/historial", headers=token_de(escenario["estudiante"])).status_code == 403
    assert cliente.get("/historial").status_code in (401, 403)


def test_filtros_por_entidad_usuario_y_fecha(cliente, escenario):
    cliente.put(f"/cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["docente"]), json={"duracion_horas": 20})
    cliente.put(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}", headers=token_de(escenario["docente"]),
                json={"nombre_evaluacion": "Cuestionario final"})
    cliente.put(f"/categorias/{escenario['categoria'].id_categoria}", headers=token_de(escenario["admin"]),
                json={"nombre_categoria": "Diseño UX"})
    assert len(_historial(cliente, escenario)) == 3
    assert [r["entidad"] for r in _historial(cliente, escenario, entidad="evaluacion")] == ["EVALUACION"]
    assert len(_historial(cliente, escenario, id_usuario=str(escenario["docente"].id_usuario))) == 2
    hoy = hoy_en_colombia()  # el filtro trabaja con el día de Colombia, no con el de la base (UTC)
    assert len(_historial(cliente, escenario, desde=str(hoy), hasta=str(hoy))) == 3
    assert _historial(cliente, escenario, hasta=str(hoy - timedelta(days=1))) == []
    r = cliente.get("/historial", headers=token_de(escenario["admin"]), params={"entidad": "FACTURA"})
    assert r.status_code == 400
