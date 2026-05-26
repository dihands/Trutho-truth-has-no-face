@echo off
echo ============================================
echo  TRUTHO — Setup Script (Windows 11)
echo ============================================

cd backend

echo.
echo [1/3] Creating Python virtual environment...
python -m venv venv

echo.
echo [2/3] Activating venv and installing packages...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [3/3] Setup complete!
echo.
echo ============================================
echo  IMPORTANT: Before running, edit .env file
echo  and set your PostgreSQL DATABASE_URL
echo ============================================
echo.
echo To start the backend server, run:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Then open frontend\index.html in your browser.
echo.
pause
