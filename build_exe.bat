@echo off
REM Optional: builds a standalone dist\HandMouse.exe (no Python needed to run it)
cd /d "%~dp0"
call venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name HandMouse --icon handmouse\assets\icon.ico ^
  --collect-all customtkinter --collect-all mediapipe --add-data "handmouse\assets;handmouse\assets" run_app.py
echo.
echo Done: dist\HandMouse.exe
pause
