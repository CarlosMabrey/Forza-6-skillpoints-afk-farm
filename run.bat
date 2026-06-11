@echo off
setlocal

cd /d "%~dp0"

set CONDA_PYTHON=C:\ProgramData\miniconda3\python.exe

echo [INFO] Starting Forza Automator...
"%CONDA_PYTHON%" auto_forza_skill_points.py %*

endlocal
