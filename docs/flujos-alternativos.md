# Flujos alternativos implementados en el MVP

Cada fila dice qué valida el backend, qué responde la API (código HTTP y mensaje), dónde está en el código y qué prueba automática lo verifica. Las rutas de código son relativas a `Backend-plataforma-de-cursos-online/src`.

Códigos HTTP que usa el sistema: **400** la petición no cumple una regla del negocio · **401** no hay sesión válida · **403** el usuario no tiene permiso o la cuenta no puede hacer eso · **404** no existe · **422** faltan datos o tienen formato inválido.

## Escenarios alternativos de las historias de usuario

### HU-01 · Inicio de Sesión y Autenticación

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: credenciales incorrectas | Si la contraseña no coincide (bcrypt), no entrega token. Mismo mensaje que para un usuario inexistente. | 401 · «Credenciales inválidas» | `services/usuario.py` → `login` | `test_login_con_contrasena_incorrecta_se_rechaza` |
| Esc. 3: usuario desactivado | Con contraseña correcta y cuenta inactiva (activo = False) niega el acceso. | 403 · «Su cuenta se encuentra desactivada. Contacte al administrador» | `services/usuario.py` → `login` | `test_login_cuenta_desactivada` |
| Esc. 4: usuario inexistente | Si el correo o el nombre de usuario no existe, responde igual que con contraseña errada. | 401 · «Credenciales inválidas» | `services/usuario.py` → `login` | `test_login_usuario_inexistente_mismo_mensaje` |

### HU-02 · Registro Público de Estudiante

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: correo ya registrado | Antes de crear la cuenta busca el correo sin distinguir mayúsculas. Si existe, no crea nada. | 400 · «El correo electrónico ya se encuentra registrado en la plataforma» | `services/usuario.py` → `crear` | `test_registro_con_correo_repetido` |
| Esc. 3: datos incompletos o formato inválido | El schema exige todos los campos, correo con formato válido y contraseña de 8 o más caracteres. El manejador devuelve el mensaje y la lista «campos» para resaltarlos. | 422 · «Por favor complete todos los campos obligatorios» | `schemas/usuario_schema.py` → `(clase UsuarioCreate)` | `test_registro_con_campos_vacios_o_correo_invalido`<br>`test_registro_solo_con_correo_mal_escrito_da_el_mensaje_de_formato` |

### HU-03 · Administración de Cuentas y Roles

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: editar perfil o cambiar rol | Solo el administrador edita datos o rol. El rol nuevo aplica en la siguiente petición porque los permisos leen el rol de la base de datos, no del token. | 200 | `services/usuario.py` → `actualizar` | `test_solo_admin_edita_o_borra_usuarios`<br>`test_admin_cambia_el_rol_y_el_permiso_aplica_de_inmediato` |
| Esc. 3: desactivar una cuenta | Pone activo = False. Desde ese momento no inicia sesión y su token anterior deja de servir. | 200 (después: 401 con token viejo y 403 al iniciar sesión) · «Token inválido» | `services/usuario.py` → `actualizar` | `test_usuario_desactivado_pierde_el_acceso_de_inmediato`<br>`test_login_cuenta_desactivada`<br>`test_admin_desactiva_por_la_api_y_el_usuario_pierde_el_acceso` |
| Esc. 4: correo duplicado al crear | Cuando crea la cuenta un administrador con sesión, el correo repetido se rechaza con el mensaje «en el sistema». | 400 · «El correo electrónico ya se encuentra registrado en el sistema» | `services/usuario.py` → `crear` | `test_admin_crea_usuario_con_correo_repetido` |

### HU-04 · Parametrización de Categorías y Cursos

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: registro exitoso de un curso | Guarda el curso y fuerza el estado BORRADOR aunque se pida otro. Si lo crea un docente, él queda como profesor; el administrador debe asignar uno. | 201 (400 si el administrador no asigna profesor) · «Debe asignar un profesor (usuario activo con rol Docente)» | `services/curso.py` → `crear` | `test_curso_nuevo_nace_en_borrador_y_con_su_profesor`<br>`test_admin_debe_asignar_profesor` |
| Esc. 3: edición de un curso existente | Actualiza descripción, duración o profesor. Solo el administrador o el profesor asignado. Deja registro en el historial (RF-07). | 200 | `services/curso.py` → `actualizar` | `test_reasignar_el_curso_le_quita_el_acceso_al_profesor_anterior`<br>`test_editar_un_curso_deja_usuario_fecha_y_detalle` |
| Esc. 4: campos requeridos incompletos | El schema exige nombre, descripción, duración mayor que 0 y categoría. Un texto con solo espacios cuenta como vacío. | 422 · «Por favor complete todos los campos obligatorios» | `schemas/curso_schema.py` → `(clase CursoCreate)` | `test_curso_con_campos_obligatorios_vacios`<br>`test_solo_espacios_cuenta_como_campo_vacio`<br>`test_editar_un_curso_con_un_campo_obligatorio_vacio` |

### HU-05 · Control de Estado y Publicación de Cursos

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: pasar a BORRADOR (despublicar) | El administrador cambia el estado a BORRADOR. El curso sale del catálogo. No se borra nada y los matriculados siguen entrando al aula. | 200 | `services/curso.py` → `actualizar` | `test_pasar_a_borrador_no_afecta_a_los_matriculados`<br>`test_publicar_u_ocultar_un_curso_tambien_se_registra` |
| Esc. 3: bloqueo de publicación (sin lecciones o datos incompletos) | Para publicar exige nombre, descripción, duración, categoría, profesor asignado y al menos una lección. | 400 · «El curso debe tener información completa y al menos una lección para ser publicado» | `services/curso.py` → `actualizar` | `test_no_se_publica_un_curso_sin_lecciones`<br>`test_no_se_publica_un_curso_sin_profesor_asignado` |

### HU-06 · Exploración del Catálogo de Cursos

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: filtrado por categoría | Con el parámetro id_categoria devuelve solo los cursos PUBLICADOS de esa categoría. | 200 | `services/curso.py` → `catalogo` | `test_catalogo_filtra_por_categoria` |
| Esc. 3: categoría sin cursos publicados | El backend devuelve una lista vacía. El mensaje del E1 lo muestra el frontend cuando la lista llega vacía. | 200 con lista vacía · «No se encontraron cursos disponibles para la categoría seleccionada» | `services/curso.py` → `catalogo` | `test_catalogo_de_una_categoria_sin_cursos_publicados_sale_vacio` |

### HU-07 · Consulta de Cursos Asignados

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: instructor sin cursos asignados | El backend lista solo los cursos donde el docente es el profesor asignado; si no tiene, devuelve lista vacía. El mensaje del E1 lo muestra el frontend. | 200 con lista vacía · «Actualmente no tienes cursos asignados. Contacta al administrador para la asignación de materias» | `services/curso.py` → `obtener_para_usuario` | `test_docente_no_toca_el_curso_de_otro_docente` |
| Esc. 3: acceso directo a la gestión del curso | El frontend navega a la pantalla de lecciones del curso. El backend entrega las lecciones del curso solo si el docente es su profesor. | 200 | `services/leccion.py` → `obtener_para_usuario` | `test_docente_ve_las_lecciones_de_su_curso_asignado`<br>`test_docente_no_ve_las_lecciones_de_un_curso_ajeno` |

### HU-09 · Procesamiento de Pago y Matrícula Automática

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: rechazo del pago por la pasarela | El adaptador traduce el código 51 a RECHAZADO. El checkout guarda el Pago rechazado y deja la inscripción en PENDIENTE (solo pasa a ACTIVA si se aprueba). | 200 con aprobado = false · «Transacción rechazada. Por favor intente con otro método de pago» | `services/checkout.py` → `pagar_curso` | `test_pago_rechazado_deja_la_inscripcion_pendiente`<br>`test_adapter_traduce_codigo_51_a_rechazado`<br>`test_la_pasarela_se_puede_cambiar_sin_tocar_el_checkout` |
| Esc. 3: matrícula previa activa | Si ya existe una inscripción ACTIVA del estudiante en el curso, no cobra ni crea otro pago. | 400 · «Ya te encuentras matriculado activamente en este curso» | `services/checkout.py` → `pagar_curso` | `test_no_se_cobra_dos_veces_si_ya_esta_matriculado` |

### HU-10 · Reporte de Estudiantes Matriculados

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: curso sin estudiantes inscritos | Si el curso no tiene inscripciones ACTIVA, APROBADA o REPROBADA, el reporte va vacío con el mensaje. PENDIENTE y CANCELADA no cuentan. | 200 · «Aún no hay estudiantes matriculados en este curso» | `endpoints/curso.py` → `estudiantes_matriculados` | `test_hu10_reporte_de_estudiantes_del_curso` |

### HU-11 · Estructuración de Lecciones y Recursos

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: asociar materiales a una lección | Guarda el material unido a una lección que existe (RN-03). Valida el tipo (PDF, VIDEO, DOCUMENTO, ENLACE) y que el enlace sea http(s) completo. | 201 (400 si el enlace o el tipo no sirven) · «El enlace del material debe ser una dirección web completa (http:// o https://)» | `services/material.py` → `crear` | `test_material_con_tipo_y_enlace_validos`<br>`test_enlace_de_material_incompleto` |
| Esc. 3: reordenar lecciones | Cambia el número de orden de una lección. El orden no se repite dentro del curso. | 200 (400 si el orden ya está ocupado) · «Ya existe una lección con este orden en el curso» | `services/leccion.py` → `actualizar` | `test_reordenar_a_un_orden_ocupado_da_mensaje_claro`<br>`test_reordenar_una_leccion_a_un_orden_libre` |
| Esc. 4: lección sin título o sin número de orden | Rechaza la lección si el título está vacío o si el orden falta o es menor que 1. | 400 · «Debe asignar un título y un número de orden a la lección» | `services/leccion.py` → `crear` | `test_leccion_sin_titulo_u_orden` |

### HU-12 · Consumo de Contenido y Progreso

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: marcar lección como completada | Registra el avance una sola vez por lección, recalcula el porcentaje y revisa si el curso ya se puede cerrar (HU-16). | 200 · «Lección marcada como completada» | `services/aula.py` → `marcar_completada` | `test_marcar_completada_actualiza_el_avance`<br>`test_con_lecciones_pendientes_no_se_cierra_y_cierra_al_completarlas` |
| Esc. 3: abrir o descargar un material | El backend entrega el enlace de cada material dentro del contenido del curso. El frontend lo abre en otra pestaña. | 200 | `services/aula.py` → `contenido_curso` | `test_contenido_en_orden_con_materiales_y_evaluacion`<br>`test_el_aula_entrega_el_enlace_del_material` |
| Esc. 4: bloqueo por inscripción PENDIENTE o CANCELADA | Solo entra al aula quien tiene la inscripción ACTIVA, APROBADA o REPROBADA. Sin inscripción, PENDIENTE o CANCELADA no ve el contenido. | 403 · «No cuenta con una inscripción activa para visualizar este contenido» | `services/aula.py` → `_inscripcion_con_acceso` | `test_inscripcion_pendiente_no_ve_el_contenido`<br>`test_admin_cancela_pero_no_aprueba` |

### HU-13 · Descarga de certificado

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: curso todavía ACTIVO (sin aprobar) | El aula informa que el certificado no está disponible (botón inhabilitado). Si igual se pide el PDF, se niega. | 403 en la descarga · 200 en el aula con certificado_disponible = false · «El certificado estará disponible una vez el curso sea aprobado» | `services/certificado.py` → `generar_documento` | `test_mensajes_del_certificado_segun_el_estado`<br>`test_sin_aprobar_no_hay_certificado` |
| Esc. 3: inscripción CANCELADA o REPROBADA | Solo con inscripción APROBADA se arma el PDF. Con CANCELADA o REPROBADA se niega. | 403 · «No cumple con las condiciones para la emisión del certificado» | `services/certificado.py` → `generar_documento` | `test_mensajes_del_certificado_segun_el_estado`<br>`test_reprobar_cierra_sin_certificado_pero_con_auditoria`<br>`test_inscripcion_cancelada_no_descarga_certificado` |

### HU-14 · Diseño e Instrumentación de Evaluaciones

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: editar preguntas o nota mínima (evaluación aún no respondida) | Deja editar la evaluación y sus preguntas solo mientras ningún estudiante la haya presentado. Si ya hay calificaciones o intentos, lo bloquea. | 200 (400 si ya fue presentada) · «La evaluación ya fue presentada por estudiantes y no se puede modificar» | `services/evaluacion.py` → `evaluacion_editable` | `test_evaluacion_presentada_ya_no_se_edita`<br>`test_editar_la_nota_minima_de_una_evaluacion_no_presentada`<br>`test_editar_la_clave_de_una_pregunta_no_presentada` |
| Esc. 3: bloqueo por parámetros inválidos (sin clave o nota mínima fuera de rango) | La nota mínima debe estar entre 0 y 5. La respuesta correcta debe ser una de las opciones (o Verdadero/Falso). | 400 · «Debe seleccionar la respuesta correcta y definir una nota de aprobación válida» | `services/evaluacion.py` → `_validar_nota_minima` | `test_nota_minima_fuera_de_rango`<br>`test_opcion_multiple_sin_clave_valida_se_rechaza`<br>`test_verdadero_falso_con_clave_invalida_se_rechaza` |

### HU-15 · Presentación de Evaluación y Calificación Automática

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: evaluación reprobada | Calcula la nota, guarda el intento (IntentoEvaluacion) y la nota vigente (Calificacion), avisa que no alcanzó la nota y deja reintentar. | 200 con aprobada = false · «No alcanzaste la nota mínima requerida. Puedes volver a intentarlo.» | `services/presentacion_evaluacion.py` → `presentar` | `test_presentar_mitad_bien_da_dos_punto_cinco_y_reprueba`<br>`test_perder_una_evaluacion_no_cierra_el_curso_y_puede_reintentar`<br>`test_evaluacion_reprobada_mensaje_exacto` |
| Esc. 3: reenvío de una evaluación ya aprobada | Si ya tiene nota aprobatoria, rechaza un nuevo envío. El resultado anterior se consulta en solo lectura con puede_presentar = false. | 400 al reenviar · 200 al consultar · «Esta evaluación ya fue aprobada; el resultado queda en modo de solo lectura» | `services/presentacion_evaluacion.py` → `presentar` | `test_resultado_en_solo_lectura_e_intentos_guardados`<br>`test_reenviar_una_evaluacion_aprobada_mensaje_exacto` |

### HU-16 · Cierre académico automático

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: cierre automático REPROBADA | Cuando todo está aprobado y completo calcula el promedio ponderado. Si es menor que 3,5 deja la inscripción REPROBADA, guarda el registro de cierre y no emite certificado. | 200 con estado_curso = REPROBADA | `services/cierre.py` → `evaluar_cierre` | `test_reprobar_cierra_sin_certificado_pero_con_auditoria`<br>`test_dip_el_observador_de_certificados_usa_la_emision_inyectada` |
| Esc. 3: curso incompleto | Si faltan evaluaciones por aprobar o lecciones por completar, no cierra: la inscripción sigue ACTIVA y el aula muestra el mensaje. | 200 · «Debes presentar todas las evaluaciones antes del cierre académico» | `services/cierre.py` → `evaluar_cierre` | `test_si_faltan_evaluaciones_no_se_cierra`<br>`test_con_lecciones_pendientes_no_se_cierra_y_cierra_al_completarlas`<br>`test_perder_una_evaluacion_no_cierra_el_curso_y_puede_reintentar` |

### HU-17 · Auditoría Administrativa de Cierres Académicos

| Escenario (Entregable 1) | Qué valida el sistema | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Esc. 2: filtrar por estado final | Con el parámetro estado devuelve solo las inscripciones de ese estado de cierre. Un estado que no es de cierre se rechaza. | 200 (400 si el filtro no es un estado de cierre) · «El filtro de cierres debe ser APROBADA, REPROBADA o FINALIZADA» | `services/inscripcion.py` → `cierres` | `test_hu17_reporte_de_cierres` |

## Otras reglas y restricciones del negocio

Reglas que se precisaron al refinar las historias en el Entregable 2 y requisitos que no tienen historia propia.

| Historia o requisito | Regla o validación | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| HU-02 | Documento repetido | 400 · «El número de documento ya se encuentra registrado en la plataforma» | `services/usuario.py` → `crear` | `test_registro_con_documento_repetido` |
| HU-02 | Nombre de usuario repetido | 400 · «El nombre de usuario ya existe» | `services/usuario.py` → `crear` | `test_registro_con_nombre_de_usuario_repetido` |
| HU-02 | El registro público siempre crea un Estudiante activo | 201 con rol = Estudiante | `endpoints/usuario.py` → `crear_usuario` | `test_registro_publico_siempre_crea_estudiante`<br>`test_registro_publico_no_puede_crear_admin_aunque_lo_pida` |
| HU-03 | El administrador no se bloquea a sí mismo | 400 · «No puede desactivarse, quitarse el rol de administrador ni eliminar su propia cuenta» | `endpoints/usuario.py` → `actualizar_usuario` | `test_el_admin_no_se_bloquea_a_si_mismo` |
| HU-04 | Un docente no edita ni borra el curso de otro | 403 · «No tiene permisos para modificar este curso» | `services/permisos.py` → `exigir_gestion_curso` | `test_docente_no_toca_el_curso_de_otro_docente`<br>`test_reasignar_el_curso_le_quita_el_acceso_al_profesor_anterior` |
| HU-04 | Categorías (crear Admin o Docente; editar o borrar solo Admin) | 403 · «No tiene permisos para realizar esta acción» | `endpoints/categoria.py` → `actualizar_categoria` | `test_docente_crea_categorias_pero_solo_el_admin_las_cambia` |
| HU-05 | Solo el administrador publica u oculta | 403 · «Solo el administrador puede publicar u ocultar un curso» | `services/curso.py` → `actualizar` | `test_solo_el_admin_publica` |
| HU-05 | Un curso publicado no se queda sin lecciones | 400 · «Un curso publicado debe tener al menos una lección; no puede eliminar la única que tiene» | `services/leccion.py` → `eliminar` | `test_curso_publicado_no_se_queda_sin_lecciones` |
| HU-09 | No se vuelve a comprar un curso ya cerrado | 400 · «Ya finalizaste este curso; no se puede volver a comprar» | `services/checkout.py` → `pagar_curso` | `test_no_se_vuelve_a_comprar_un_curso_aprobado` |
| HU-09 | Datos del medio de pago inválidos | 400 · «El número de tarjeta debe tener 16 dígitos» | `patrones/pagos.py` → `validar` | `test_datos_invalidos_se_rechazan_antes_de_cobrar`<br>`test_tarjeta_no_envia_el_numero_completo` |
| HU-09 | Medio de pago no soportado | 400 · «Medio de pago no soportado: …» | `patrones/pagos.py` → `obtener_estrategia` | `test_cada_medio_tiene_su_estrategia` |
| HU-09 | Curso inexistente o no publicado | 400 · «El curso no existe o no está publicado» | `services/checkout.py` → `pagar_curso` | `test_no_se_paga_un_curso_no_publicado_o_inexistente` |
| HU-09 | Solo un Estudiante compra | 403 · «No tiene permisos para realizar esta acción» | `endpoints/checkout.py` → `pagar_curso` | `test_docente_no_compra_cursos` |
| HU-11 | Tipo de material no permitido | 400 · «El tipo de material debe ser PDF, VIDEO, DOCUMENTO o ENLACE» | `services/material.py` → `_validar_datos` | `test_material_con_tipo_no_permitido` |
| HU-11 | Material sin lección existente (RN-03) | 400 · «La lección no existe» | `services/material.py` → `_leccion_permitida` | `test_material_en_una_leccion_que_no_existe` |
| HU-12 | Después del cierre el avance ya no cambia | 403 · «No cuenta con una inscripción activa para visualizar este contenido» | `services/aula.py` → `marcar_completada` | `test_despues_del_cierre_no_cambia_el_avance` |
| HU-14 | Los porcentajes del curso no pasan de 100 % | 400 · «Los porcentajes de las evaluaciones del curso no pueden pasar de 100 % (ya hay {usado:g} %)» | `services/evaluacion.py` → `_validar_suma_porcentajes` | `test_porcentajes_del_curso_no_pasan_de_100` |
| HU-14 | Una evaluación por lección (RN-03) | 400 · «Esta lección ya tiene una evaluación» | `services/evaluacion.py` → `crear` | `test_segunda_evaluacion_en_la_misma_leccion` |
| HU-14 | Tipo de pregunta desconocido y pregunta mal armada | 400 · «Tipo de pregunta no soportado: …» | `patrones/factory_preguntas.py` → `obtener_creador` | `test_tipo_desconocido_se_rechaza` |
| HU-14 | El estudiante no crea preguntas ni ve la clave; el docente no ve la clave de otro curso | 403 (rol) · 404 (curso ajeno) · «Evaluación no encontrada» | `endpoints/pregunta.py` → `listar_preguntas_con_clave` | `test_estudiante_no_puede_crear_preguntas`<br>`test_docente_no_ve_preguntas_con_clave_de_otro_curso` |
| HU-15 | Sin inscripción ACTIVA no presenta ni ve las preguntas | 403 · «No cuenta con una inscripción activa para presentar esta evaluación» | `services/presentacion_evaluacion.py` → `_evaluacion_e_inscripcion` | `test_sin_inscripcion_activa_no_puede_presentar`<br>`test_sin_inscripcion_no_ve_las_preguntas` |
| HU-15 | Evaluación sin preguntas o inexistente | 400 · «La evaluación todavía no tiene preguntas» | `services/presentacion_evaluacion.py` → `presentar` | `test_presentar_una_evaluacion_sin_preguntas`<br>`test_presentar_una_evaluacion_que_no_existe` |
| HU-13 / RF-16 | Nadie emite, edita ni borra certificados a mano | 405 | `endpoints/certificado.py` | `test_el_administrador_no_puede_emitir_certificados_a_mano`<br>`test_certificados_pagos_y_notas_no_se_editan_a_mano` |
| RF-17 | Verificar un certificado con un código falso | 404 · «No existe un certificado con ese código» | `endpoints/certificado.py` → `verificar_certificado` | `test_verificar_certificado_por_codigo` |
| RF-10 | Cancelar una inscripción que no está PENDIENTE ni ACTIVA; matrícula manual inválida | 400 · «Solo se puede cancelar una inscripción PENDIENTE o ACTIVA» | `services/inscripcion.py` → `cancelar` | `test_cp15_no_se_cancela_una_inscripcion_aprobada`<br>`test_cp16_no_se_cancela_una_inscripcion_reprobada` |
| RF-07 | Historial: solo lo consulta el administrador | 403 · 401 · «No tiene permisos para realizar esta acción» | `endpoints/historial.py` | `test_el_historial_lo_consulta_solo_el_administrador` |
| RF-07 | Historial: una edición sin cambios reales no deja registro | 200 | `services/historial.py` → `describir_cambios` | `test_sin_cambios_reales_no_se_registra_nada` |
| RF-07 | Historial: filtro de entidad inválido | 400 · «La entidad debe ser una de: …» | `services/historial.py` → `buscar` | `test_filtros_por_entidad_usuario_y_fecha` |
| RF-07 | Historial: fecha inicial mayor que la final | 400 · «La fecha inicial no puede ser mayor que la fecha final» | `services/historial.py` → `buscar` | `test_historial_con_fecha_inicial_mayor_que_la_final` |

## Validaciones que aplican a todo el sistema

| Situación | Respuesta de la API | Dónde está en el código | Prueba automática |
|---|---|---|---|
| Campo obligatorio faltante, vacío o con solo espacios | 422 · «Por favor complete todos los campos obligatorios» (con la lista `campos`) | `app.py` → `datos_invalidos`; `schemas/base_schema.py` → `EntradaSchema` | `test_solo_espacios_cuenta_como_campo_vacio` |
| Formato inválido (correo, número fuera de rango, identificador mal escrito, rol desconocido) | 422 · «Hay datos con formato inválido. Revise los campos marcados» | `app.py` → `datos_invalidos` | `test_identificador_mal_escrito_en_la_ruta_responde_422` |
| Petición sin sesión | 401 · «Debe iniciar sesión para realizar esta acción» | `endpoints/deps.py` → `get_current_user_id` | `test_peticion_sin_token_responde_401_en_espanol` |
| Token falso, alterado, vencido (dura 2 horas) o de un usuario desactivado | 401 · «Token inválido» | `utils/jwt_utils.py`; `endpoints/deps.py` → `obtener_usuario_actual` | `test_token_invalido_mensaje_exacto`, `test_token_vencido_responde_401` |
| Rol sin permiso para la ruta (RN-02) | 403 · «No tiene permisos para realizar esta acción» | `endpoints/deps.py` → `requiere_rol` | `test_rol_no_permitido_mensaje_exacto` |
| Docente sobre un curso que no es suyo (RN-02) | 403 · «No tiene permisos para modificar este curso» / 404 al consultar | `services/permisos.py` → `exigir_gestion_curso` | `test_docente_no_modifica_el_contenido_de_un_curso_ajeno` |
| Borrar algo que tiene registros asociados | 400 con el mensaje de cada caso | `endpoints/usuario.py`; `services/categoria.py`, `curso.py`, `leccion.py` → `eliminar` | `test_no_se_elimina_una_categoria_con_cursos` |
| Filtros de consulta inválidos | 400 · «La fecha inicial no puede ser posterior a la fecha final» / «Estado no válido. Use uno de: …» | `services/pago.py`, `services/inscripcion.py` | `test_filtros_invalidos_mensaje_exacto` |
| Recurso inexistente | 404 con el mensaje de cada módulo | `src/endpoints` | `test_recurso_inexistente_responde_404` |
| Arranque sin `SECRET_KEY` o sin `DATABASE_URL` | La API no arranca y dice qué variable falta | `utils/jwt_utils.py`, `database/config.py` | `test_sin_configuracion_la_aplicacion_no_arranca` |
