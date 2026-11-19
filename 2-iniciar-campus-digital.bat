@echo off
chcp 65001 >nul
title Campus Digital - Iniciar
cd /d "%~dp0"

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] No se encontro Node.js. Instalalo desde nodejs.org, version LTS.
  pause
  exit /b 1
)
if not exist "Backend-plataforma-de-cursos-online\venv" (
  echo [ERROR] Primero abre "1-preparar-base-de-datos.bat".
  pause
  exit /b 1
)

echo Encendiendo la API (backend)...
start "API Campus Digital - NO CERRAR" /d "%~dp0Backend-plataforma-de-cursos-online" cmd /k "call venv\Scripts\activate.bat && python main.py"

echo Encendiendo la pagina (frontend). La primera vez instala librerias y tarda unos minutos...
start "Pagina Campus Digital - NO CERRAR" /d "%~dp0Frontend-plataforma-de-cursos-online\web" cmd /k "(if not exist node_modules npm install) & npm start"

echo.
echo Cuando la ventana de la pagina diga "Local: http://localhost:4200", abre ese enlace.
echo Usuarios (clave Clave123*): admin / Ana Torres / carlos.ruiz@campusdigital.co / lucia.martinez@email.com
echo Para apagar todo, cierra las dos ventanas negras que se abrieron.
echo.
pause
