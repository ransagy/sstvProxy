@echo off
pyinstaller sstvProxy.py --onefile -i sstv.ico
robocopy ".\dist" ".\Windows" "sstvproxy.exe"
robocopy "." ".\Windows" "version.txt"
pause