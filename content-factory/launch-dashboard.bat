@echo off
title Content Factory Dashboard
color 0B
echo.
echo   ==============================
echo    Content Factory Dashboard
echo   ==============================
echo.

cd /d "D:\Projects\my-project\content-factory"

:: Kill anything already on port 3000
echo   Checking port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING" 2^>nul') do (
    echo   Killing old process PID %%a...
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo   Starting on http://localhost:3000/studio
echo   Press Ctrl+C to stop
echo.

:: Open browser to /studio after a short delay
start "" cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:3000/studio"

:: Start the dashboard
npm run dashboard
