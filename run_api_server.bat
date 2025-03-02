@echo off
echo Video Compressor API Server
echo =========================

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting API server...
echo Access the web interface at http://localhost:5000
echo.
python api_server.py

pause 