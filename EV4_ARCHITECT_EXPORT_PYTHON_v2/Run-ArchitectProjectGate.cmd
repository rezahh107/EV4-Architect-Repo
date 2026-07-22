@echo off
setlocal
cd /d "%~dp0"

where py.exe >nul 2>nul
if %ERRORLEVEL%==0 (
  py.exe -3 "%~dp0Generate-ArchitectProjectGate.py"
) else (
  python.exe "%~dp0Generate-ArchitectProjectGate.py"
)

set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo Export failed with exit code %RC%.
) else (
  echo Export completed successfully.
)
pause
exit /b %RC%
