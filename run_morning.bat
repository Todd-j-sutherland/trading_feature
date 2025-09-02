@echo off
echo Running Trading System Morning Routine...
cd /d "c:\Users\todd.sutherland\trading_feature"
set PYTHONPATH=c:\Users\todd.sutherland\trading_feature

REM Try different Python locations
echo Trying python from virtual environment...
"c:\Users\todd.sutherland\trading_feature\trading_venv\bin\python.exe" -m app.main morning 2>nul && goto :success

echo Trying system python...
python -m app.main morning 2>nul && goto :success

echo Trying python3...
python3 -m app.main morning 2>nul && goto :success

echo Trying py launcher...
py -m app.main morning 2>nul && goto :success

echo.
echo ❌ Could not find a working Python installation
echo Please ensure Python is installed and the virtual environment is properly configured
echo.
echo Manual command to try:
echo cd "c:\Users\todd.sutherland\trading_feature"
echo set PYTHONPATH=c:\Users\todd.sutherland\trading_feature
echo python -m app.main morning
pause
goto :end

:success
echo ✅ Morning routine completed successfully!
pause

:end
