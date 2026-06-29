@echo off
cd /d "%~dp0"
echo Cleaning stale git locks (OneDrive)...
del /f /q ".git\index.lock" ".git\config.lock" ".git\HEAD.lock" 2>nul
git config --global --add safe.directory "%CD%" 2>nul
git remote remove origin 2>nul
git remote add origin https://github.com/barraver94-spec/avuka.git
git add -A
git -c user.name="avuka-deploy" -c user.email="bar@avuka.co.il" commit -m "deploy: generic calibrated renderer (forms 1-3)"
git branch -M main
git push -u origin main --force
echo.
echo ===================================================
echo   DONE - check above for errors. HEAD should update.
echo ===================================================
pause
