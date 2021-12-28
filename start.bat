@echo off
color a
title moist bot

:a
cls
".\venv\Scripts\python.exe" main.py

echo Bot closed. Restart?
pause
goto a