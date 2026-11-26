@echo off
title Rojgar Setu (रोजगार सेतु) - P2P Platform Launcher
color 0A

echo =========================================================================
echo      ROJGAR SETU (रोजगार सेतु) - PRODUCTION MASTER P2P LAUNCHER
echo      Django 5+ ^| PostgreSQL (Supabase) ^| Gemini Flash ^| PostGIS
echo =========================================================================
echo.

cd /d "%~dp0"

:: Activate virtual environment if present
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist "..\venv\Scripts\activate.bat" (
    call "..\venv\Scripts\activate.bat"
)

echo [1/3] Checking dependencies & applying database migrations on Supabase...
python manage.py makemigrations core
python manage.py migrate

echo [2/3] Seeding demo vocational trades, karigars, and pre-signed contracts...
python manage.py seed_p2p_data

echo [3/3] Starting Django Development Server on port 8000...
echo.
echo =========================================================================
echo   Open in your browser: http://127.0.0.1:8000/
echo   Worker:   Phone: 9870001111   Password: password123
echo   Employer: Phone: 9811223344   Password: password123
echo =========================================================================
echo.

python manage.py runserver 8000
pause
