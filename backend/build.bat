@echo off
REM Build script for Hotel AI Backend Docker image (Windows)

echo ================================
echo Building Hotel AI Backend Docker Image
echo ================================

set IMAGE_NAME=hotel-ai-backend
set VERSION=1.0.0

echo Building image: %IMAGE_NAME%:%VERSION%

REM Build from backend directory
cd /d "%~dp0"

REM Build the image
docker build -t %IMAGE_NAME%:%VERSION% -t %IMAGE_NAME%:latest .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build complete!
    echo.
    echo Run the container with:
    echo   docker run -p 8000:8000 %IMAGE_NAME%:latest
    echo.
    echo Or use docker-compose:
    echo   docker-compose up -d
    echo.
    echo Check health:
    echo   curl http://localhost:8000/health
) else (
    echo Build failed!
    exit /b 1
)
