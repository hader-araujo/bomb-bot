@echo off
python --version 3>NUL
if errorlevel 1 goto errorNoPython

pip install -r requirements.txt
python main.py

:errorNoPython
echo Error^: Python not installed