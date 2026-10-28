@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
if not exist ".venv\Scripts\python.exe" (%PY% -m venv .venv || goto error)
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto error
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto error
exit /b 0
:error
echo Ohjelman kaynnistys epaonnistui.
pause
exit /b 1
