@echo off
chcp 65001 >nul
title Campus Digital - Preparar la base de datos
echo ============================================================
echo   Campus Digital - Paso 1: preparar la base de datos (Neon)
echo ============================================================
cd /d "%~dp0Backend-plataforma-de-cursos-online"

rem Python puede llamarse "py" o "python" segun como se instalo
set "PY="
py -3 --version >nul 2>nul && set "PY=py -3"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (
  echo [ERROR] No se encontro Python. Instalalo desde python.org y marca "Add Python to PATH".
  pause
  exit /b 1
)
echo Usando Python:
%PY% --version
if not exist ".env" (
  echo [ERROR] No esta el archivo .env en la carpeta del backend.
  pause
  exit /b 1
)

if not exist venv (
  echo Creando el entorno virtual...
  %PY% -m venv venv
)
call venv\Scripts\activate.bat

echo.
echo Instalando las librerias del backend (la primera vez tarda unos minutos)...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt -r requirements-dev.txt
if errorlevel 1 goto error

echo.
echo Creando las tablas en Neon...
python migrardb.py
if errorlevel 1 goto error

echo.
echo Cargando los datos de demostracion...
python datos_demo.py
if errorlevel 1 goto error

echo.
echo ============================================================
echo   LISTO. Ahora abre "2-iniciar-campus-digital.bat"
echo ============================================================
pause
exit /b 0

:error
echo.
echo [ERROR] Algo fallo. Copia el mensaje de arriba y mandaselo a Claude.
pause
exit /b 1
