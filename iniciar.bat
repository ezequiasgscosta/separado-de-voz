@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Instalando o aplicativo...
    call instalar.bat
    if errorlevel 1 exit /b 1
)

if not exist ".venv\Scripts\pythonw.exe" (
    echo O ambiente virtual nao foi criado corretamente. Execute instalar.bat novamente.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -c "import numpy, demucs.separate, imageio_ffmpeg" >nul 2>nul
if errorlevel 1 (
    echo Dependencias ausentes. Instalando ou reparando o aplicativo...
    call instalar.bat
    if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" -c "import numpy, demucs.separate, imageio_ffmpeg" >nul 2>nul
if errorlevel 1 (
    echo As dependencias de audio ainda nao estao disponiveis.
    echo Confira a conexao com a internet e execute instalar.bat novamente.
    pause
    exit /b 1
)

".venv\Scripts\pythonw.exe" app.py
