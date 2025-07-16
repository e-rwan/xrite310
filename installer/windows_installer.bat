@echo off
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Erreur : Python n'est pas installe ou non present dans le PATH.
    pause
    exit /b 1
)

echo Lancement de l'installation des dependances...
python install_dependencies.py
pause
