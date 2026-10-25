@echo off
setlocal
cd /d "%~dp0"
title 15BPM_PMRN - Testar conexao Google Sheets
if not exist ".venv\Scripts\python.exe" (
  echo Execute primeiro 1_INSTALAR_DEPENDENCIAS.bat.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" check_google_access.py
pause
