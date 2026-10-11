@echo off
echo ========================================================
echo   Starting YT Shorts Management System (Full Stack)
echo ========================================================
echo.
echo Launching Backend in a new window...
start "YT Shorts - Backend" cmd /k "call start_backend.bat"

echo Launching Frontend in a new window...
start "YT Shorts - Frontend" cmd /k "call start_frontend.bat"

echo.
echo ========================================================
echo  Both services launched!
echo  - Frontend UI:  http://localhost:3000
echo  - Backend API:  http://localhost:8000/docs
echo ========================================================
pause
