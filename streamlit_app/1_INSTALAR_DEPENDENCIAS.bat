@echo off
setlocal
cd /d "%~dp0"
title 15BPM_PMRN - Instalar dependencias

echo ======================================================
echo  15BPM_PMRN - Instalacao inicial
echo ======================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERRO: Python Launcher nao encontrado.
  echo Instale Python 3.11 ou 3.12 em https://www.python.org/downloads/windows/
  echo Durante a instalacao, marque a opcao para adicionar o Python ao PATH.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Nao foi possivel criar o ambiente virtual.
    pause
    exit /b 1
  )
)

echo Atualizando pip e instalando bibliotecas...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo.
echo Instalacao concluida.
echo Agora configure a conta de servico do Google seguindo o README.md.
pause
exit /b 0

:erro
echo.
echo A instalacao falhou. Confira a conexao com a internet e a versao do Python.
pause
exit /b 1
