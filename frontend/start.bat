@echo off
echo ====================================
echo  (Banana Slides) 
echo ====================================
echo.

echo [1/3] ...
if not exist "node_modules\" (
    echo , ...
    call npm install
    if errorlevel 1 (
        echo , : npm install
        pause
        exit /b 1
    )
) else (
    echo 
)

echo.
echo [2/3] ...
echo.
echo [3/3] ...
echo  http://localhost:3011
echo  http://localhost:5011
echo.
echo  Ctrl+C 
echo.

call npm run dev

pause