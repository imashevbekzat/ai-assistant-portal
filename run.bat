@echo off
setlocal
set PYTHON=C:\Users\8_lenovo\AppData\Local\Programs\Python\Python312\python.exe
cd /d %~dp0
"%PYTHON%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
