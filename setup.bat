@echo off
title HandMouse - setup
cd /d "%~dp0"
echo ============================================
echo   HandMouse setup
echo ============================================
set PYCMD=
for %%V in (3.12 3.11 3.10 3.9) do (
  if not defined PYCMD (
    py -%%V -c "import sys" >nul 2>nul && set PYCMD=py -%%V
  )
)
if not defined PYCMD (
  echo.
  echo [ERROR] Python 3.9 - 3.12 was not found.
  echo Install Python 3.12 from https://www.python.org/downloads/windows/
  echo and keep the "py launcher" option ticked. Then run setup.bat again.
  echo ^(Python 3.13 and newer are NOT supported by MediaPipe yet.^)
  pause
  exit /b 1
)
echo Using: %PYCMD%
%PYCMD% -m venv venv || (echo Failed to create the virtual environment & pause & exit /b 1)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Install failed - check your internet connection & pause & exit /b 1)

echo.
echo Creating a desktop shortcut...
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\HandMouse.lnk'); $s.TargetPath='%~dp0venv\Scripts\pythonw.exe'; $s.Arguments='-m handmouse'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0handmouse\assets\icon.ico'; $s.Description='HandMouse'; $s.Save()"
echo.
echo ============================================
echo   Done!  Double-click run.bat or the new
echo   "HandMouse" icon on your desktop.
echo ============================================
pause
