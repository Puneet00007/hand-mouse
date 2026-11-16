@echo off
REM Optional: start HandMouse automatically when you sign in to Windows.
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\HandMouse.lnk"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%~dp0venv\Scripts\pythonw.exe'; $s.Arguments='-m handmouse'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0handmouse\assets\icon.ico'; $s.Save()"
echo Startup shortcut created. To undo, delete HandMouse from the folder opened by:  Win+R  ->  shell:startup
pause
