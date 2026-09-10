@echo off
echo ===================================================
echo   SagarDrishti Marine Intelligence Stack Launcher  
echo ===================================================
echo.

echo Starting FastAPI Backend Server on http://127.0.0.1:8000 ...
start "SagarDrishti Backend API" cmd /k ".venv\Scripts\python.exe -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React Vite Frontend on http://localhost:5173 ...
start "SagarDrishti React Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers launching! 
echo Access Frontend UI: http://localhost:5173
echo Access API Docs:    http://127.0.0.1:8000/docs
echo ===================================================
