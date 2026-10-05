@echo off
rem Chay demo D3 tren Windows: cai thu vien, chay test, mo giao dien.
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -q pandas networkx streamlit plotly pyyaml pytest
if errorlevel 1 (
  echo Khong cai duoc thu vien. Kiem tra Python 3.10+ va ket noi mang.
  pause
  exit /b 1
)
python -m pytest -q
if errorlevel 1 echo CANH BAO: co test that bai - van mo giao dien de xem.
python -m streamlit run app.py
pause
