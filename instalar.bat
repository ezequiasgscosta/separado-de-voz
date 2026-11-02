@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Instale o Python 3.10 ou superior e marque "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Nao foi possivel atualizar o pip.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo A instalacao das dependencias falhou.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import numpy, demucs.separate, imageio_ffmpeg"
if errorlevel 1 (
    echo A instalacao terminou, mas nao foi possivel carregar as dependencias de audio.
    echo Confira a conexao com a internet e tente novamente.
    pause
    exit /b 1
)

echo.
echo Instalacao concluida. Abra iniciar.bat para usar o aplicativo.
pause
