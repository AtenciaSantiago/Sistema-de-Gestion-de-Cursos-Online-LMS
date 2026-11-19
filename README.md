# Campus Digital · Sistema de Gestión de Cursos Online (LMS)

Proyecto de aula del curso **Diseño de Sistemas de Información** · Instituto Tecnológico Metropolitano (ITM).
Docente: **Alexandra Guerrero Bocanegra**. Entregable 3 · noviembre de 2026.

Repositorio de entrega: https://github.com/AtenciaSantiago/Sistema-de-Gestion-de-Cursos-Online-LMS

## ¿Qué hace el sistema?

Plataforma donde un estudiante compra un curso en línea, estudia sus lecciones, presenta las evaluaciones, el sistema lo califica y cierra el curso solo y, si aprueba, descarga su certificado. El docente arma los cursos, las lecciones, los materiales y las evaluaciones; el administrador gestiona usuarios y audita pagos, inscripciones y cierres.

## Integrantes

- Santiago Atencia Ortiz
- Samuel Montoya Galeano
- Diego Mauricio Castañeda
- Luis Alejandro Saldarriaga
- Mauricio Alejandro Velásquez Mercado

## Tecnologías

| Parte | Tecnología |
|---|---|
| Frontend | Angular 20 + Angular Material (TypeScript) |
| Backend (API REST) | Python · FastAPI · SQLAlchemy · Pydantic |
| Base de datos | PostgreSQL (Neon) |
| Seguridad | Contraseñas con bcrypt + token JWT (PyJWT) |
| Certificados | PDF generado con fpdf2 |
| Pruebas | pytest |
| Control de versiones | Git y GitHub |

## Arquitectura

El sistema tiene tres partes (contenedores del nivel 2 del modelo C4): la **aplicación web** en Angular, la **API REST** en FastAPI y la **base de datos** PostgreSQL. La API es un solo proceso organizado por capas (`endpoints` → `services` → `entities`) y por componentes de negocio.

| Componente de la API | Qué hace | Historias y requisitos |
|---|---|---|
| Seguridad y usuarios | Inicio de sesión, registro, cuentas, token y permisos por rol | HU-01, HU-02, HU-03 |
| Cursos y categorías | Crear, editar y publicar cursos; cursos del docente | HU-04, HU-05, HU-07, HU-10 |
| Lecciones y materiales | Contenido del curso | HU-11 |
| Evaluaciones y preguntas | Diseño, presentación y calificación (Factory Method) | HU-14, HU-15 |
| Aula virtual y progreso | Lecciones completadas, avance y descarga del certificado | HU-12, HU-13 |
| Catálogo y pagos | Catálogo público y pago en línea (Strategy y Adapter) | HU-06, HU-09 |
| Cierre académico | Promedio ponderado y estado final (Observer) | HU-16 |
| Certificados | Emisión con código único y PDF (Template Method) | HU-13, RF-17 |
| Auditoría administrativa | Inscripciones, pagos, cierres, certificados e historial | HU-17, RF-07, RF-10, RF-11 |
| Acceso a datos | Modelos y conexión con SQLAlchemy | Todos |

Los diagramas UML de componentes y de despliegue, con su correspondencia con el código, están en [`docs/arquitectura.md`](docs/arquitectura.md).

### Estructura del repositorio

```
Sistema-de-Gestion-de-Cursos-Online-LMS/
├── Backend-plataforma-de-cursos-online/
│   ├── src/entities/    tablas (SQLAlchemy)
│   ├── src/schemas/     lo que entra y sale de la API (Pydantic)
│   ├── src/services/    reglas de negocio
│   ├── src/endpoints/   rutas de la API
│   ├── src/patrones/    los 5 patrones GoF
│   ├── tests/           pruebas automáticas
│   ├── migrardb.py      crea/actualiza las tablas
│   └── datos_demo.py    datos de demostración
├── Frontend-plataforma-de-cursos-online/web/   aplicación Angular
└── docs/                documentación técnica del Entregable 3 (diagramas UML, matrices, evidencias)
```

## Funcionalidades e historias de usuario

Numeración del documento del Entregable 1. Están implementadas las 13 historias del MVP y las 3 del Release 2 (HU-03, HU-10 y HU-17). La HU-08 (gestión manual de inscripciones) se eliminó en el arreglo del E1: el pago y el cierre cambian el estado de la inscripción solos; al administrador solo le quedan la matrícula manual y la cancelación (RF-10).

| HU | Descripción | Rol | API |
|---|---|---|---|
| HU-01 | Inicio de sesión con correo o usuario | Todos | `POST /usuarios/login` |
| HU-02 | Registro público (siempre como estudiante) | Visitante | `POST /usuarios` |
| HU-03 | Administración de cuentas y roles | Admin | `/usuarios` |
| HU-04 | Categorías y cursos (todo curso nace en BORRADOR) | Admin, Docente | `/categorias`, `/cursos` |
| HU-05 | Publicar u ocultar un curso | Admin | `PUT /cursos/{id}` (`estado_curso`) |
| HU-06 | Catálogo con filtro por categoría | Estudiante | `GET /catalogo` |
| HU-07 | Mis cursos asignados | Docente | `GET /cursos` |
| HU-09 | Pago en línea y matrícula automática | Estudiante | `POST /checkout/cursos/{id}` |
| HU-10 | Estudiantes matriculados en mi curso | Docente | `GET /cursos/{id}/estudiantes` |
| HU-11 | Lecciones y materiales | Docente | `/lecciones`, `/material` |
| HU-12 | Consumo de contenido y progreso | Estudiante | `/mis-cursos` |
| HU-13 | Descarga y verificación del certificado | Estudiante / público | `GET /mis-cursos/{id}/certificado`, `GET /certificados/verificar/{codigo}` |
| HU-14 | Diseño de evaluaciones y sus preguntas | Docente | `/evaluaciones`, `POST /evaluaciones/{id}/preguntas` |
| HU-15 | Presentar evaluación y calificación automática | Estudiante | `POST /evaluaciones/{id}/presentar`, `GET /evaluaciones/{id}/mi-resultado` |
| HU-16 | Cierre académico automático | Sistema | ocurre al presentar la última evaluación |
| HU-17 | Auditoría de cierres académicos | Admin | `GET /inscripciones/cierres` |
| RF-10 / RF-11 | Matrícula manual, cancelación y auditoría de pagos | Admin | `/inscripciones`, `GET /pago` |
| RF-07 | Historial de cambios de contenidos (quién, cuándo y qué cambió; sin HU en el E1) | Admin | `GET /historial` |

Cada historia tiene implementados sus flujos alternativos (validaciones, reglas de negocio y errores controlados): ver [`docs/flujos-alternativos.md`](docs/flujos-alternativos.md).

## Patrones de diseño (GoF) implementados

| Patrón | Tipo | Dónde | Para qué |
|---|---|---|---|
| Factory Method | Creacional | `src/patrones/factory_preguntas.py` | Crear cada tipo de pregunta (opción múltiple, verdadero/falso) |
| Strategy | Comportamiento | `src/patrones/pagos.py` | Pagar con tarjeta o con PSE |
| Adapter | Estructural | `src/patrones/pagos.py` | Traducir la pasarela de pagos externa a nuestro sistema |
| Observer | Comportamiento | `src/patrones/cierre_academico.py` | Avisar a auditoría y a certificados cuando se cierra un curso |
| Template Method | Comportamiento | `src/patrones/certificado_generador.py` | Fijar el orden de los pasos del certificado en cada formato (PDF y texto) |

Los cinco están verificados con pruebas automáticas (`pytest`), incluidas pruebas de sustitución (LSP) para las estrategias de pago, los tipos de pregunta y los generadores del certificado. Donde bastaba una función (coordinar la compra, el historial de cambios, la sesión de base de datos) no se usó patrón.

## Requisitos

- Python 3 y `pip`.
- Node.js en una versión compatible con Angular 20 (20.19 o superior) y `npm`.
- Una base de datos PostgreSQL (el equipo usa Neon, que es gratuito).
- Git.

## Configuración

Dependencias: `Backend-plataforma-de-cursos-online/requirements.txt` (API), `requirements-dev.txt` (pruebas) y `Frontend-plataforma-de-cursos-online/web/package.json` (aplicación web).

El backend lee su configuración de un archivo `.env` dentro de `Backend-plataforma-de-cursos-online/` (no se sube al repositorio):

```
DATABASE_URL=postgresql://usuario:clave@servidor/basedatos
SECRET_KEY=una-clave-larga-y-secreta
ALGORITHM=HS256
```

Si falta `DATABASE_URL` o `SECRET_KEY`, la API no arranca y dice cuál falta. La dirección de la API que usa la aplicación web está en `Frontend-plataforma-de-cursos-online/web/src/environments/environment.ts` (por defecto `http://127.0.0.1:8000`).

## Cómo ejecutarlo

### En Windows, con dos clics

1. `1-preparar-base-de-datos.bat`: crea el entorno de Python, pide la cadena de conexión (`.env`), crea las tablas y carga los datos de demostración.
2. `2-iniciar-campus-digital.bat`: enciende la API (puerto 8000) y la aplicación web (http://localhost:4200).
3. (Opcional) `3-agregar-quiz-python.bat`: agrega una guía y un quiz al curso «Introducción a Python».

### Backend (paso a paso)

```bash
cd Backend-plataforma-de-cursos-online
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python migrardb.py        # crea las tablas
python datos_demo.py      # (opcional, base vacía) datos de demostración
uvicorn src.app:app --reload
```

Documentación interactiva de la API: http://127.0.0.1:8000/docs

### Frontend

```bash
cd Frontend-plataforma-de-cursos-online/web
npm install
npm start                 # http://localhost:4200
```

### Pruebas automáticas

```bash
cd Backend-plataforma-de-cursos-online
pip install -r requirements-dev.txt
pytest
```

## Usuarios de demostración (`datos_demo.py`)

Contraseña de todos: `Clave123*`

| Usuario | Rol |
|---|---|
| admin | Administrador |
| Ana Torres | Docente (profesora de los cursos de demostración) |
| Carlos Ruiz | Docente sin cursos asignados (muestra el mensaje de la HU-07) |
| Lucía Martínez | Estudiante (sin inscribir, para mostrar la compra) |

Pasarela de pagos **simulada** (no cobra dinero real): la tarjeta `4242 4242 4242 4242` se aprueba; una tarjeta terminada en `0002` se rechaza.

## Despliegue

El MVP se ejecuta en local: la aplicación web y la API corren en el computador de la demostración y la base de datos está en la nube (Neon). No hay un despliegue público. El diagrama de despliegue está en [`docs/arquitectura.md`](docs/arquitectura.md).

## Documentación y diagramas

Toda la documentación técnica del Entregable 3 está en la carpeta [`docs/`](docs/README.md). Cada diagrama tiene su imagen y su archivo editable (`.drawio`).

| Documento | Contenido |
|---|---|
| [`docs/maquina-de-estados.md`](docs/maquina-de-estados.md) | Máquina de estados de la inscripción: diagrama, matriz de análisis, transiciones rechazadas y casos de prueba |
| [`docs/arquitectura.md`](docs/arquitectura.md) | Diagramas UML de componentes y de despliegue |
| [`docs/secuencia/`](docs/secuencia) | Siete diagramas de secuencia (al menos uno por épica) con su flujo principal y sus flujos alternativos |
| [`docs/flujos-alternativos.md`](docs/flujos-alternativos.md) | Flujos alternativos por historia: qué valida el sistema, qué responde, dónde está en el código y qué prueba lo verifica |

## Evidencias

- **Pruebas automáticas:** 232 pruebas con pytest. La salida de su ejecución está en [`docs/evidencias/`](docs/evidencias/README.md).
- **Máquina de estados:** cada transición tiene su caso de prueba (CP-01 a CP-25) en `tests/test_maquina_estados_inscripcion.py`.
- **Flujos alternativos:** archivos `tests/test_alt_*.py`, uno por épica.
- **Flujos principales y alternativos en pantalla:** capturas en el documento consolidado del proyecto (secciones 4 y 11).
