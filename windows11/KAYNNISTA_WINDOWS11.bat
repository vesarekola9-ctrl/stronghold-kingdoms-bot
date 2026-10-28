@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SHK Scout Windows 11 - Kaynnistin
echo ============================================
echo SHK Scout Windows 11 - Kaynnistys
echo ============================================
echo Kansio: %CD%
echo.
if not exist "scout_engine.py" (
 echo VIRHE: scout_engine.py puuttuu.
 echo Lataa koko windows11-port-haara, ei yksittaisia tiedostoja.
 goto error
)
if not exist "..\stronghold_kingdoms_bot\templates\bags\bag.png" (
 echo VIRHE: Resurssikuvat puuttuvat.
 echo Pura GitHubista ladattu KOKO ZIP, ei vain windows11-kansiota.
 goto error
)
set "PYTHON_CMD="
where py >nul 2>&1
if not errorlevel 1 (
 py -3.12 -c "import sys" >nul 2>&1
 if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
 where python >nul 2>&1
 if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
 echo VIRHE: Python ei loydy. Asenna Python 3.12 ja valitse Add to PATH.
 goto error
)
if not exist ".venv\Scripts\python.exe" (
 echo Luodaan virtuaaliymparisto...
 %PYTHON_CMD% -m venv ".venv"
 if errorlevel 1 goto error
)
echo Asennetaan tai tarkistetaan kirjastot...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto error
echo Kaynnistetaan botti...
".venv\Scripts\python.exe" app.py 1> "shk_stdout.log" 2> "shk_error.log"
if errorlevel 1 (
 echo VIRHE: Ohjelma kaatui. Katso windows11\shk_error.log
 type "shk_error.log"
 goto error
)
echo Ohjelma suljettu normaalisti.
pause
exit /b 0
:error
echo.
echo Kaynnistys epaonnistui. Kopioi ylla oleva virhe tai shk_error.log.
pause
exit /b 1
