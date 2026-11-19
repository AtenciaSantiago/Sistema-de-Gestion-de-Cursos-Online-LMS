"""
Arranca la API FastAPI con uvicorn.

  python main.py

Documentación interactiva: http://127.0.0.1:8000/docs

Para crear o actualizar las tablas en la base de datos, usa primero: python migrardb.py
"""

import uvicorn

if __name__ == "__main__":
    # Se pasa la app como texto ("src.app:app") porque reload=True lo exige
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )