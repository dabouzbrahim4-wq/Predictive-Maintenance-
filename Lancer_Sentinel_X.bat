@echo off
setlocal
cd /d "%~dp0"
title Sentinel-X Maintenance Console

echo.
echo ==========================================
echo   Sentinel-X Maintenance Console
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python est introuvable. Installez Python 3.10+ puis relancez ce fichier.
    echo.
    pause
    exit /b 1
)

python -c "import streamlit, pandas, plotly, firebase_admin, streamlit_autorefresh" >nul 2>nul
if errorlevel 1 (
    echo Installation des dependances Python...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Echec de l'installation des dependances.
        echo Verifiez votre connexion Internet puis relancez ce fichier.
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Lancement de l'application...
echo Si le navigateur ne s'ouvre pas automatiquement, utilisez l'adresse affichee par Streamlit.
echo.

python -m streamlit run app.py

echo.
pause
