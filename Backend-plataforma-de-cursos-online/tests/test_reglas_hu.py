"""
Pruebas de la auditoría del Entregable 2: cada prueba revisa un escenario de una HU
(con el mensaje exacto del E1) o un permiso por rol (RN-02).
"""

from conftest import crear_usuario, token_de
from src.entities.Curso import Curso
from src.entities.Pago import Pago
from src.entities.inscripcion import EstadoInscripcion


def _docente2(db):
    return crear_usuario(db, "Carlos Ruiz", "carlos.ruiz@campus.co", "400", "Docente")


# ------------------------------- HU-01 -------------------------------------
def test_login_con_correo_electronico(cliente, escenario):
    r = cliente.post("/usuarios/login", json={"nombre_usuario": "LUCIA.MARTINEZ@email.com", "contrasena": "Clave123*"})
    assert r.status_code == 200 and r.json()["rol"] == "Estudiante"


def test_login_usuario_inexistente_mismo_mensaje(cliente, escenario):
    r = cliente.post("/usuarios/login", json={"nombre_usuario": "nadie@email.com", "contrasena": "Clave123*"})
    assert r.status_code == 401 and r.json()["detail"] == "Credenciales inválidas"


def test_login_cuenta_desactivada(cliente, db, escenario):
    escenario["estudiante"].activo = False
    db.commit()
    r = cliente.post("/usuarios/login", json={"nombre_usuario": "lucia.martinez@email.com", "contrasena": "Clave123*"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Su cuenta se encuentra desactivada. Contacte al administrador"


def test_usuario_desactivado_pierde_el_acceso_de_inmediato(cliente, db, escenario):
    """HU-03 esc. 3: aunque tenga un token viejo, ya no entra."""
    token = token_de(escenario["estudiante"])
    escenario["estudiante"].activo = False
    db.commit()
    assert cliente.get("/mis-cursos", headers=token).status_code == 401


# ------------------------------- HU-02 -------------------------------------
def test_registro_con_correo_repetido(cliente, escenario):
    r = cliente.post("/usuarios", json={
        "nombre_usuario": "Otra Lucía", "tipo_documento": "CC", "documento_identidad": "999",
        "email": "lucia.martinez@email.com", "contrasena": "Clave123*", "rol": "Estudiante",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "El correo electrónico ya se encuentra registrado en la plataforma"


def test_admin_crea_usuario_con_correo_repetido(cliente, escenario):
    """HU-03 esc. 4: cuando lo crea el administrador, el mensaje del E1 dice «en el sistema»."""
    r = cliente.post("/usuarios", headers=token_de(escenario["admin"]), json={
        "nombre_usuario": "Otra Lucía", "tipo_documento": "CC", "documento_identidad": "999",
        "email": "lucia.martinez@email.com", "contrasena": "Clave123*", "rol": "Docente",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "El correo electrónico ya se encuentra registrado en el sistema"


def test_registro_con_campos_vacios_o_correo_invalido(cliente, escenario):
    r = cliente.post("/usuarios", json={"nombre_usuario": "", "email": "no-es-correo", "contrasena": "x"})
    assert r.status_code == 422
    assert r.json()["detail"] == "Por favor complete todos los campos obligatorios"
    assert "email" in r.json()["campos"]  # para que el front resalte los campos


# ------------------------------- HU-04 -------------------------------------
def _curso_nuevo(**extra):
    return {
        "nombre_curso": "UX Writing",
        "descripcion_curso": "Textos claros para interfaces",
        "duracion_horas": 8,
        "precio": 50,
        **extra,
    }


def test_curso_nuevo_nace_en_borrador_y_con_su_profesor(cliente, escenario):
    r = cliente.post(
        "/cursos",
        headers=token_de(escenario["docente"]),
        json=_curso_nuevo(id_categoria=str(escenario["categoria"].id_categoria), estado_curso="PUBLICADO"),
    )
    assert r.status_code == 201
    assert r.json()["estado_curso"] == "BORRADOR"  # aunque pida PUBLICADO
    assert r.json()["nombre_docente"] == "Ana Torres"


def test_admin_debe_asignar_profesor(cliente, escenario):
    r = cliente.post("/cursos", headers=token_de(escenario["admin"]),
                     json=_curso_nuevo(id_categoria=str(escenario["categoria"].id_categoria)))
    assert r.status_code == 400 and "profesor" in r.json()["detail"]


def test_curso_con_campos_obligatorios_vacios(cliente, escenario):
    r = cliente.post("/cursos", headers=token_de(escenario["docente"]), json={"nombre_curso": "Sin datos"})
    assert r.status_code == 422
    assert r.json()["detail"] == "Por favor complete todos los campos obligatorios"


def test_estudiante_no_puede_crear_cursos(cliente, escenario):
    r = cliente.post("/cursos", headers=token_de(escenario["estudiante"]),
                     json=_curso_nuevo(id_categoria=str(escenario["categoria"].id_categoria)))
    assert r.status_code == 403


def test_docente_no_toca_el_curso_de_otro_docente(cliente, db, escenario):
    otro = _docente2(db)
    url = f"/cursos/{escenario['curso'].id_curso}"
    assert cliente.put(url, headers=token_de(otro), json={"duracion_horas": 1}).status_code == 403
    assert cliente.delete(url, headers=token_de(otro)).status_code == 403
    assert cliente.get("/cursos", headers=token_de(otro)).json() == []  # HU-07: solo ve los suyos


# ------------------------------- HU-05 -------------------------------------
def test_solo_el_admin_publica(cliente, db, escenario):
    escenario["curso"].estado_curso = "BORRADOR"
    db.commit()
    url = f"/cursos/{escenario['curso'].id_curso}"
    r = cliente.put(url, headers=token_de(escenario["docente"]), json={"estado_curso": "PUBLICADO"})
    assert r.status_code == 403
    r = cliente.put(url, headers=token_de(escenario["admin"]), json={"estado_curso": "PUBLICADO"})
    assert r.status_code == 200 and r.json()["estado_curso"] == "PUBLICADO"


def test_no_se_publica_un_curso_sin_lecciones(cliente, db, escenario):
    vacio = Curso(id_categoria=escenario["categoria"].id_categoria, nombre_curso="Vacío", descripcion_curso="x",
                  duracion_horas=2, estado_curso="BORRADOR", id_docente=escenario["docente"].id_usuario,
                  id_usuario_creacion=escenario["docente"].id_usuario)
    db.add(vacio)
    db.commit()
    r = cliente.put(f"/cursos/{vacio.id_curso}", headers=token_de(escenario["admin"]), json={"estado_curso": "PUBLICADO"})
    assert r.status_code == 400
    assert r.json()["detail"] == "El curso debe tener información completa y al menos una lección para ser publicado"


def test_pasar_a_borrador_no_afecta_a_los_matriculados(cliente, db, escenario):
    url = f"/cursos/{escenario['curso'].id_curso}"
    cliente.put(url, headers=token_de(escenario["admin"]), json={"estado_curso": "BORRADOR"})
    assert cliente.get("/catalogo").json() == []  # salió del catálogo
    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert aula.status_code == 200  # pero Lucía sigue estudiando


# ------------------------------- HU-11 -------------------------------------
def test_leccion_sin_titulo_u_orden(cliente, escenario):
    r = cliente.post("/lecciones", headers=token_de(escenario["docente"]),
                     json={"id_curso": str(escenario["curso"].id_curso), "titulo_leccion": "", "duracion_horas": 1})
    assert r.status_code == 400
    assert r.json()["detail"] == "Debe asignar un título y un número de orden a la lección"


def test_reordenar_a_un_orden_ocupado_da_mensaje_claro(cliente, escenario):
    r = cliente.post("/lecciones", headers=token_de(escenario["docente"]),
                     json={"id_curso": str(escenario["curso"].id_curso), "titulo_leccion": "Color", "orden": 2})
    assert r.status_code == 201
    r = cliente.put(f"/lecciones/{r.json()['id_leccion']}", headers=token_de(escenario["docente"]), json={"orden": 1})
    assert r.status_code == 400 and "orden" in r.json()["detail"]


def test_material_con_tipo_y_enlace_validos(cliente, escenario):
    base = {"id_leccion": str(escenario["leccion"].id_leccion), "titulo_material": "Guía"}
    malo = cliente.post("/material", headers=token_de(escenario["docente"]),
                        json={**base, "tipo_material": "PDF", "URL_archivo": "archivo.pdf"})
    assert malo.status_code == 400
    bueno = cliente.post("/material", headers=token_de(escenario["docente"]),
                         json={**base, "tipo_material": "pdf", "URL_archivo": "https://campus.co/guia.pdf"})
    assert bueno.status_code == 201 and bueno.json()["tipo_material"] == "PDF"


# ------------------------------- HU-14 -------------------------------------
def test_nota_minima_fuera_de_rango(cliente, db, escenario):
    r = cliente.put(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}",
                    headers=token_de(escenario["docente"]), json={"nota_minima": 7})
    assert r.status_code == 400
    assert r.json()["detail"] == "Debe seleccionar la respuesta correcta y definir una nota de aprobación válida"


def test_porcentajes_del_curso_no_pasan_de_100(cliente, escenario):
    r = cliente.post("/lecciones", headers=token_de(escenario["docente"]),
                     json={"id_curso": str(escenario["curso"].id_curso), "titulo_leccion": "Color", "orden": 2})
    r = cliente.post("/evaluaciones", headers=token_de(escenario["docente"]),
                     json={"id_leccion": r.json()["id_leccion"], "nombre_evaluacion": "Extra", "porcentaje": 10})
    assert r.status_code == 400 and "100" in r.json()["detail"]


def test_evaluacion_presentada_ya_no_se_edita(cliente, escenario):
    ev = escenario["evaluacion"].id_evaluacion
    p = cliente.post(f"/evaluaciones/{ev}/preguntas", headers=token_de(escenario["docente"]),
                     json={"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?", "respuesta_correcta": "verdadero"}).json()
    assert p["respuesta_correcta"] == "Verdadero"  # la Factory la deja escrita igual siempre
    cliente.post(f"/evaluaciones/{ev}/presentar", headers=token_de(escenario["estudiante"]),
                 json={"respuestas": {p["id_pregunta"]: "Falso"}})
    r = cliente.put(f"/preguntas/{p['id_pregunta']}", headers=token_de(escenario["docente"]),
                    json={"respuesta_correcta": "Falso"})
    assert r.status_code == 400 and "no se puede modificar" in r.json()["detail"]
    editable = cliente.get(f"/evaluaciones/{ev}/editable", headers=token_de(escenario["docente"])).json()
    assert editable["editable"] is False


# ------------------------------- HU-15 -------------------------------------
def test_resultado_en_solo_lectura_e_intentos_guardados(cliente, escenario):
    ev = escenario["evaluacion"].id_evaluacion
    p = cliente.post(f"/evaluaciones/{ev}/preguntas", headers=token_de(escenario["docente"]),
                     json={"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?", "respuesta_correcta": "Verdadero"}).json()
    estudiante = token_de(escenario["estudiante"])
    cliente.post(f"/evaluaciones/{ev}/presentar", headers=estudiante, json={"respuestas": {p["id_pregunta"]: "Falso"}})
    cliente.post(f"/evaluaciones/{ev}/presentar", headers=estudiante, json={"respuestas": {p["id_pregunta"]: "Verdadero"}})

    resultado = cliente.get(f"/evaluaciones/{ev}/mi-resultado", headers=estudiante).json()
    assert resultado["aprobada"] is True and resultado["puede_presentar"] is False
    assert [i["nota"] for i in resultado["intentos"]] == [0.0, 5.0]  # RF-13: quedaron los dos intentos

    otra_vez = cliente.post(f"/evaluaciones/{ev}/presentar", headers=estudiante, json={"respuestas": {}})
    assert otra_vez.status_code == 400  # ya estaba aprobada


def test_sin_inscripcion_no_ve_las_preguntas(cliente, db, escenario):
    intruso = crear_usuario(db, "Pedro", "pedro@email.com", "500", "Estudiante")
    r = cliente.get(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas", headers=token_de(intruso))
    assert r.status_code == 403


# ------------------------------- HU-09 -------------------------------------
def test_no_se_vuelve_a_comprar_un_curso_aprobado(cliente, db, escenario):
    escenario["inscripcion"].estado_inscripcion = EstadoInscripcion.APROBADA.value
    db.commit()
    r = cliente.post(f"/checkout/cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]),
                     json={"metodo_pago": "TARJETA", "numero_tarjeta": "4242424242424242", "titular": "Lucía"})
    assert r.status_code == 400
    db.refresh(escenario["inscripcion"])
    assert escenario["inscripcion"].estado_inscripcion == "APROBADA"  # no se le borró el resultado


def test_docente_no_compra_cursos(cliente, escenario):
    r = cliente.post(f"/checkout/cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["docente"]),
                     json={"metodo_pago": "PSE", "banco": "BANCOLOMBIA", "tipo_persona": "NATURAL"})
    assert r.status_code == 403


# ------------------------------- HU-13 / RF-17 -----------------------------
def test_mensajes_del_certificado_segun_el_estado(cliente, db, escenario):
    url = f"/mis-cursos/{escenario['curso'].id_curso}"
    estudiante = token_de(escenario["estudiante"])
    aula = cliente.get(url, headers=estudiante).json()
    assert aula["certificado_disponible"] is False
    assert aula["mensaje_certificado"] == "El certificado estará disponible una vez el curso sea aprobado"

    escenario["inscripcion"].estado_inscripcion = EstadoInscripcion.REPROBADA.value
    db.commit()
    r = cliente.get(f"{url}/certificado", headers=estudiante)
    assert r.status_code == 403
    assert r.json()["detail"] == "No cumple con las condiciones para la emisión del certificado"


def test_verificar_certificado_por_codigo(cliente, escenario):
    ev = escenario["evaluacion"].id_evaluacion
    p = cliente.post(f"/evaluaciones/{ev}/preguntas", headers=token_de(escenario["docente"]),
                     json={"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?", "respuesta_correcta": "Verdadero"}).json()
    cliente.post(f"/evaluaciones/{ev}/presentar", headers=token_de(escenario["estudiante"]),
                 json={"respuestas": {p["id_pregunta"]: "Verdadero"}})
    codigo = cliente.get("/inscripciones?estado=APROBADA", headers=token_de(escenario["admin"])).json()[0]["codigo_certificado"]

    r = cliente.get(f"/certificados/verificar/{codigo.lower()}")  # público, sin sesión
    assert r.status_code == 200 and r.json()["estudiante"] == "Lucía Martínez"
    assert cliente.get("/certificados/verificar/CERT-FALSO").status_code == 404


def test_certificados_pagos_y_notas_no_se_editan_a_mano(cliente, escenario):
    admin = token_de(escenario["admin"])
    falso = "00000000-0000-0000-0000-000000000000"
    assert cliente.put(f"/certificados/{falso}", headers=admin, json={}).status_code == 405
    assert cliente.post("/pago", headers=admin, json={}).status_code == 405
    assert cliente.post("/calificaciones", headers=admin, json={}).status_code == 405


# ------------------------------- RF-10 / RF-11 -----------------------------
def test_admin_cancela_pero_no_aprueba(cliente, escenario):
    admin = token_de(escenario["admin"])
    url = f"/inscripciones/{escenario['inscripcion'].id_inscripcion}"
    assert cliente.put(url, headers=admin, json={"estado_inscripcion": "APROBADA"}).status_code == 405
    r = cliente.put(f"{url}/cancelar", headers=admin)
    assert r.status_code == 200 and r.json()["estado_inscripcion"] == "CANCELADA"
    aula = cliente.get(f"/mis-cursos/{escenario['curso'].id_curso}", headers=token_de(escenario["estudiante"]))
    assert aula.status_code == 403  # RF-09: cancelada ya no ve el contenido


def test_matricula_manual_queda_activa(cliente, db, escenario):
    nuevo = crear_usuario(db, "Pedro", "pedro@email.com", "500", "Estudiante")
    r = cliente.post("/inscripciones", headers=token_de(escenario["admin"]),
                     json={"id_curso": str(escenario["curso"].id_curso), "id_usuario_inscrito": str(nuevo.id_usuario)})
    assert r.status_code == 201 and r.json()["estado_inscripcion"] == "ACTIVA"


def test_auditoria_de_pagos_con_filtros(cliente, db, escenario):
    db.add(Pago(id_usuario=escenario["estudiante"].id_usuario, id_curso=escenario["curso"].id_curso, monto=120,
                estado_pago="APROBADO", metodo_pago="TARJETA", id_usuario_creacion=escenario["estudiante"].id_usuario))
    db.commit()
    admin = token_de(escenario["admin"])
    por_curso = cliente.get(f"/pago?id_curso={escenario['curso'].id_curso}", headers=admin).json()
    assert len(por_curso) == 1 and por_curso[0]["nombre_estudiante"] == "Lucía Martínez"
    assert cliente.get("/pago?desde=2000-01-01&hasta=2000-01-02", headers=admin).json() == []
    assert cliente.get("/pago", headers=token_de(escenario["docente"])).status_code == 403


# ------------------------------- Ataques de permisos (RN-02) ---------------
def test_estudiante_no_entra_a_nada_administrativo(cliente, escenario):
    t = token_de(escenario["estudiante"])
    for metodo, ruta in [
        ("get", "/usuarios"), ("get", "/inscripciones"), ("get", "/pago"), ("get", "/certificados"),
        ("get", "/calificaciones"), ("get", "/cursos"), ("get", "/lecciones"), ("get", "/material"),
        ("get", "/evaluaciones"), ("post", "/categorias"),
    ]:
        assert getattr(cliente, metodo)(ruta, headers=t).status_code == 403, ruta


def test_sin_token_no_hay_acceso(cliente, escenario):
    for ruta in ["/usuarios", "/cursos", "/mis-cursos", "/inscripciones", "/pago"]:
        assert cliente.get(ruta).status_code in (401, 403), ruta
    assert cliente.get("/cursos", headers={"Authorization": "Bearer token-falso"}).status_code == 401


def test_docente_no_ve_preguntas_con_clave_de_otro_curso(cliente, db, escenario):
    otro = _docente2(db)
    r = cliente.get(f"/evaluaciones/{escenario['evaluacion'].id_evaluacion}/preguntas/clave", headers=token_de(otro))
    assert r.status_code == 404


def test_registro_publico_no_puede_crear_admin_aunque_lo_pida(cliente, db, escenario):
    r = cliente.post("/usuarios", json={
        "nombre_usuario": "Hacker", "tipo_documento": "CC", "documento_identidad": "666",
        "email": "hacker@email.com", "contrasena": "Clave123*", "rol": "Admin", "activo": True,
    })
    assert r.status_code == 201 and r.json()["rol"] == "Estudiante"


# ------------------------------- Segunda pasada de la auditoría ------------
def _aprobar_el_curso(cliente, escenario):
    ev = escenario["evaluacion"].id_evaluacion
    p = cliente.post(f"/evaluaciones/{ev}/preguntas", headers=token_de(escenario["docente"]),
                     json={"tipo": "VERDADERO_FALSO", "enunciado": "¿Sí?", "respuesta_correcta": "Verdadero"}).json()
    return cliente.post(f"/evaluaciones/{ev}/presentar", headers=token_de(escenario["estudiante"]),
                        json={"respuestas": {p["id_pregunta"]: "Verdadero"}}).json()


def test_reasignar_el_curso_le_quita_el_acceso_al_profesor_anterior(cliente, db, escenario):
    otro = _docente2(db)
    url = f"/cursos/{escenario['curso'].id_curso}"
    r = cliente.put(url, headers=token_de(escenario["admin"]), json={"id_docente": str(otro.id_usuario)})
    assert r.json()["nombre_docente"] == "Carlos Ruiz"
    assert cliente.put(url, headers=token_de(escenario["docente"]), json={"duracion_horas": 3}).status_code == 403
    assert cliente.put(url, headers=token_de(otro), json={"duracion_horas": 3}).status_code == 200


def test_el_certificado_lleva_el_profesor_asignado_no_quien_creo_el_curso(cliente, db, escenario):
    from src.patrones.certificado_generador import GeneradorCertificadoTexto
    from src.services.certificado import generar_documento
    escenario["curso"].id_usuario_creacion = escenario["admin"].id_usuario  # lo creó el admin
    db.commit()
    _aprobar_el_curso(cliente, escenario)
    texto, _ = generar_documento(db, escenario["estudiante"].id_usuario, escenario["curso"].id_curso,
                                 GeneradorCertificadoTexto())
    assert "Ana Torres" in texto and "admin" not in texto


def test_el_admin_no_se_bloquea_a_si_mismo(cliente, escenario):
    admin = escenario["admin"]
    url = f"/usuarios/{admin.id_usuario}"
    assert cliente.put(url, headers=token_de(admin), json={"activo": False}).status_code == 400
    assert cliente.put(url, headers=token_de(admin), json={"rol": "Estudiante"}).status_code == 400
    assert cliente.delete(url, headers=token_de(admin)).status_code == 400
    assert cliente.put(url, headers=token_de(admin), json={"tipo_documento": "CE"}).status_code == 200


def test_curso_publicado_no_se_queda_sin_lecciones(cliente, db, escenario):
    from src.entities.Evaluacion import Evaluacion
    db.query(Evaluacion).delete()  # sin evaluación, para que solo choque con la regla de la HU-05
    db.commit()
    r = cliente.delete(f"/lecciones/{escenario['leccion'].id_leccion}", headers=token_de(escenario["docente"]))
    assert r.status_code == 400 and "al menos una lección" in r.json()["detail"]


def test_solo_espacios_cuenta_como_campo_vacio(cliente, escenario):
    r = cliente.post("/cursos", headers=token_de(escenario["docente"]),
                     json=_curso_nuevo(id_categoria=str(escenario["categoria"].id_categoria), nombre_curso="    "))
    assert r.status_code == 422
    assert r.json()["detail"] == "Por favor complete todos los campos obligatorios"


def test_despues_del_cierre_no_cambia_el_avance(cliente, escenario):
    assert _aprobar_el_curso(cliente, escenario)["estado_curso"] == "APROBADA"
    r = cliente.post(f"/mis-cursos/lecciones/{escenario['leccion'].id_leccion}/completar",
                     headers=token_de(escenario["estudiante"]))
    assert r.status_code == 403


def test_docente_crea_categorias_pero_solo_el_admin_las_cambia(cliente, escenario):
    docente, admin = token_de(escenario["docente"]), token_de(escenario["admin"])
    r = cliente.post("/categorias", headers=docente, json={"nombre_categoria": "Programación"})
    assert r.status_code == 201
    url = f"/categorias/{r.json()['id_categoria']}"
    assert cliente.put(url, headers=docente, json={"nombre_categoria": "Otra"}).status_code == 403
    assert cliente.delete(url, headers=docente).status_code == 403
    assert cliente.delete(url, headers=admin).status_code == 200


def test_hu07_muestra_el_numero_de_lecciones(cliente, escenario):
    cursos = cliente.get("/cursos", headers=token_de(escenario["docente"])).json()
    assert cursos[0]["numero_lecciones"] == 1 and cursos[0]["nombre_categoria"] == "Diseño digital"


def test_hu10_reporte_de_estudiantes_del_curso(cliente, db, escenario):
    url = f"/cursos/{escenario['curso'].id_curso}/estudiantes"
    r = cliente.get(url, headers=token_de(escenario["docente"])).json()
    assert r["estudiantes"][0]["email"] == "lucia.martinez@email.com"
    assert r["estudiantes"][0]["porcentaje_avance"] == 0 and r["mensaje"] is None
    assert cliente.get(url, headers=token_de(_docente2(db))).status_code == 404  # no es su curso

    # Un estudiante que ya cerró el curso sigue en el reporte (con su estado); antes salía «sin estudiantes»
    escenario["inscripcion"].estado_inscripcion = EstadoInscripcion.APROBADA.value
    db.commit()
    cerrado = cliente.get(url, headers=token_de(escenario["docente"])).json()
    assert cerrado["estudiantes"][0]["estado_inscripcion"] == "APROBADA" and cerrado["mensaje"] is None

    escenario["inscripcion"].estado_inscripcion = EstadoInscripcion.CANCELADA.value
    db.commit()
    vacio = cliente.get(url, headers=token_de(escenario["docente"])).json()
    assert vacio["estudiantes"] == [] and vacio["mensaje"] == "Aún no hay estudiantes matriculados en este curso"


def test_hu17_reporte_de_cierres(cliente, escenario):
    admin = token_de(escenario["admin"])
    assert cliente.get("/inscripciones/cierres", headers=admin).json() == []  # Lucía sigue ACTIVA
    _aprobar_el_curso(cliente, escenario)
    cierres = cliente.get("/inscripciones/cierres?estado=aprobada", headers=admin).json()
    assert len(cierres) == 1 and cierres[0]["promedio_final"] == 5.0
    assert cierres[0]["codigo_certificado"].startswith("CERT-")
    assert cliente.get("/inscripciones/cierres?estado=ACTIVA", headers=admin).status_code == 400
    assert cliente.get("/inscripciones/cierres", headers=token_de(escenario["docente"])).status_code == 403


def test_filtros_invalidos_dan_mensaje_claro(cliente, escenario):
    admin = token_de(escenario["admin"])
    assert cliente.get("/pago?desde=2026-10-10&hasta=2026-10-01", headers=admin).status_code == 400
    assert cliente.get("/inscripciones?estado=PERDIDA", headers=admin).status_code == 400


def test_enlace_de_material_incompleto(cliente, escenario):
    r = cliente.post("/material", headers=token_de(escenario["docente"]), json={
        "id_leccion": str(escenario["leccion"].id_leccion), "titulo_material": "Video",
        "tipo_material": "VIDEO", "URL_archivo": "https://"})
    assert r.status_code == 400
