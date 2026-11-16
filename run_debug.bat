@echo off
REM Same as run.bat but keeps a console window open so you can see error messages.
cd /d "%~dp0"
venv\Scripts\python.exe -m handmouse %*
pause
