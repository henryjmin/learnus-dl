@echo off
python -m venv build-venv
call build-venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -r requirements.txt
pyinstaller -F learnus-dl.py
