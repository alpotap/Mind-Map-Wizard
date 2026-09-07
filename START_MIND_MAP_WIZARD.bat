@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python was not found. Install Python 3, then run this file again.
        pause
        exit /b 1
    )
    set "PYTHON=python"
)

start "" "http://127.0.0.1:8001"
%PYTHON% local_server.py
