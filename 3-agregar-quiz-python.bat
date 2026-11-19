@echo off
chcp 65001 >nul
title Campus Digital - Agregar quiz al curso de Python
cd /d "%~dp0Backend-plataforma-de-cursos-online"
if not exist venv (
  echo [ERROR] Primero abre "1-preparar-base-de-datos.bat".
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
python agregar_quiz_python.py
echo.
pause
