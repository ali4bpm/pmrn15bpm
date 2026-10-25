@echo off
setlocal
cd /d "%~dp0"
title 15BPM_PMRN

if not exist ".venv\Scripts\python.exe" (
  echo O ambiente virtual ainda nao existe.
  echo Execute primeiro 1_INSTALAR_DEPENDENCIAS.bat.
  pause
  exit /b 1
)
if not exist ".streamlit\secrets.toml" (
  echo ATENCAO: nao encontrei .streamlit\secrets.toml.
  echo Copie .streamlit\secrets.toml.example para secrets.toml e configure a senha administrativa.
  echo A chave da conta de servico deve ficar em .streamlit\google-service-account.json.
  pause
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
