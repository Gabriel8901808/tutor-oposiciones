@echo off
REM === Instalacion inicial (solo se ejecuta una vez) ===
cd /d "%~dp0"

echo.
echo === Creando entorno virtual de Python ===
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: No se encuentra Python. Instalalo desde la Microsoft Store
        echo o desde https://www.python.org/downloads/ marcando "Add to PATH".
        pause
        exit /b 1
    )
)

echo.
echo === Instalando dependencias ===
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo === Comprobando clave de API ===
if not exist ".streamlit\secrets.toml" (
    if not exist ".streamlit" mkdir ".streamlit"
    echo ANTHROPIC_API_KEY = "PEGA-AQUI-TU-CLAVE-sk-ant-..." > ".streamlit\secrets.toml"
    echo.
    echo Se ha creado el archivo .streamlit\secrets.toml
    echo ABRELO y pega tu clave de Anthropic antes de usar la app.
    notepad ".streamlit\secrets.toml"
)

echo.
echo === Instalacion terminada ===
echo Ya puedes hacer doble clic en "Tutor Oposiciones.bat" del Escritorio.
pause
