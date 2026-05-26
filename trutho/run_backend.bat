@echo off
echo ============================================
echo  TRUTHO — Starting Backend Server
echo ============================================
cd backend
call venv\Scripts\activate.bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
