@echo off
title Media Performance Anomaly Detector
echo Starting Media Performance Anomaly Detector...
echo.

cd /d "C:\Users\L108410\OneDrive - Eli Lilly and Company\Desktop\Hackathon"

"C:\Users\L108410\OneDrive - Eli Lilly and Company\Desktop\MMM Insights Generator\.venv\Scripts\streamlit.exe" run app.py --server.port 8502

echo.
echo Server stopped. Press any key to exit.
pause >nul
