# Documentación técnica · Entregable 3

Documentación del proyecto **Campus Digital** que acompaña al documento consolidado. Cada diagrama está en imagen (`.png`) y en su archivo editable de draw.io (`.drawio`), que se abre en https://app.diagrams.net.

| Documento | Qué contiene |
|---|---|
| [`maquina-de-estados.md`](maquina-de-estados.md) | Máquina de estados de la inscripción: diagrama, estados, matriz de análisis, transiciones rechazadas y casos de prueba (CP-01 a CP-25) |
| [`arquitectura.md`](arquitectura.md) | Diagrama de componentes UML y diagrama de despliegue UML, con su correspondencia con el código |
| [`flujos-alternativos.md`](flujos-alternativos.md) | Flujos alternativos por historia de usuario, reglas del negocio adicionales y validaciones generales, cada uno con su prueba automática |
| [`evidencias/`](evidencias/README.md) | Salida de la ejecución de las pruebas automáticas |

## Diagramas de secuencia

Hay al menos un diagrama por épica. Cada uno tiene su flujo principal, sus flujos alternativos en fragmentos combinados (`alt`, `opt`, `loop`) y las clases reales del código.

| Diagrama | Épica | Historia | Patrón |
|---|---|---|---|
| [SD-1](secuencia/SD-1-HU-01-Inicio-de-sesion.md) | EP-01 Autenticación y cuentas | HU-01 Inicio de sesión | — |
| [SD-2](secuencia/SD-2-HU-05-Publicar-curso.md) | EP-02 Administración y catálogo | HU-05 Publicación de cursos | — |
| [SD-3](secuencia/SD-3-HU-09-Pago-y-matricula.md) | EP-03 Pagos e inscripciones | HU-09 Pago y matrícula automática | Strategy y Adapter |
| [SD-4](secuencia/SD-4-HU-12-Marcar-leccion.md) | EP-04 Contenido y aprendizaje | HU-12 Consumo de contenido y progreso | — |
| [SD-5](secuencia/SD-5-HU-15-Presentar-evaluacion.md) | EP-05 Evaluación y certificación | HU-15 Presentación y calificación | Factory Method |
| [SD-6](secuencia/SD-6-HU-16-Cierre-academico.md) | EP-05 Evaluación y certificación | HU-16 Cierre académico automático | Observer |
| [SD-7](secuencia/SD-7-HU-13-Descargar-certificado.md) | EP-05 Evaluación y certificación | HU-13 Descarga de certificado | Template Method |

## Archivos editables

| Diagrama | Archivo |
|---|---|
| Máquina de estados | [`diagramas/Maquina-de-estados-Inscripcion.drawio`](diagramas/Maquina-de-estados-Inscripcion.drawio) |
| Componentes | [`diagramas/Diagrama-de-componentes-UML.drawio`](diagramas/Diagrama-de-componentes-UML.drawio) |
| Despliegue | [`diagramas/Diagrama-de-despliegue-UML.drawio`](diagramas/Diagrama-de-despliegue-UML.drawio) |
| Secuencia (SD-1 a SD-7) | carpeta [`secuencia/`](secuencia) |
