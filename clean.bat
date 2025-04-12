@echo off
if exist build-venv rmdir /q /s build-venv
if exist build rmdir /q /s build
if exist dist rmdir /q /s dist
if exist *.spec del *.spec
