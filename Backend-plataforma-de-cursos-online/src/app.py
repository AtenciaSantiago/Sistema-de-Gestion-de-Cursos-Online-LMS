"""
Aplicación FastAPI de Campus Digital. Ejecutar con:
    uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database.config import create_tables
from src.endpoints import (
    aula,
    calificacion,
    categoria,
    certificado,
    checkout,
    curso,
    evaluacion,
    historial,
    inscripcion,
    leccion,
    material,
    pago,
    pregunta,
    usuario,
)
import src.entities.intento_evaluacion  # noqa: F401 - Entregable 2: registra la tabla de intentos (RF-13)
import src.entities.registro_cierre  # noqa: F401 - Entregable 2: registra la tabla de auditoría de cierres
import src.entities.historial_cambio  # noqa: F401 - Entregable 2: historial de cambios de contenidos (RF-07)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas al iniciar la aplicación."""
    create_tables()
    yield


app = FastAPI(
    title="Campus Digital - Sistema de Gestión de Cursos Online",
    description="API REST del LMS: usuarios, cursos, lecciones, evaluaciones, pagos, inscripciones y certificados.",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS: deja que el frontend de Angular (puerto 4200) le hable a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def datos_invalidos(request: Request, exc: RequestValidationError):
    """
    Entregable 2: cuando faltan datos o vienen mal (HU-02 esc. 3 y HU-04 esc. 4) se responde
    un mensaje claro en español y la lista de campos con error, para que el front los resalte.
    """
    errores = exc.errors()
    campos = sorted({str(e["loc"][-1]) for e in errores if e.get("loc")})
    faltan_datos = any(e.get("type") in ("missing", "string_too_short") for e in errores)
    mensaje = (
        "Por favor complete todos los campos obligatorios"
        if faltan_datos
        else "Hay datos con formato inválido. Revise los campos marcados"
    )
    return JSONResponse(
        status_code=422,  # datos que no se pueden procesar (el nombre de la constante cambia según la versión)
        content=jsonable_encoder({"detail": mensaje, "campos": campos, "errores": errores}),
    )


app.include_router(usuario.router)
app.include_router(categoria.router)
app.include_router(curso.router)
app.include_router(leccion.router)
app.include_router(material.router)
app.include_router(evaluacion.router)
app.include_router(pregunta.router)  # Entregable 2: preguntas y presentación (Factory Method)
app.include_router(checkout.router)  # Entregable 2: catálogo y pago del estudiante (Strategy + Adapter)
app.include_router(aula.router)  # Entregable 2: aula virtual y progreso del estudiante (HU-12)
app.include_router(inscripcion.router)
app.include_router(pago.router)
app.include_router(calificacion.router)
app.include_router(certificado.router)
app.include_router(historial.router)  # Entregable 2: historial de cambios de contenidos (RF-07, solo Admin)


@app.get("/")
def inicio():
    return {"mensaje": "API de Campus Digital - Sistema de Gestión de Cursos Online", "docs": "/docs"}
