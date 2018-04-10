@echo off
pyinstaller sstvProxy.py --onefile -i sstv.ico
robocopy ".\dist" ".\Windows" "sstvproxy.exe"
pause