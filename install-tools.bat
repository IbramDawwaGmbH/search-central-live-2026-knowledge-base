@echo off
rem Run once. Installs what this knowledge base needs on this computer:
rem   Git for Windows, Python 3.12, the Python packages in requirements.txt, and Chromium for Playwright.
rem Everything comes from the official sources through winget and pip. Safe to run again.
setlocal
cd /d "%~dp0"
set "WINGET=1"
where winget >nul 2>nul || set "WINGET="
echo.
echo === 1 of 4: Git for Windows ===
where git >nul 2>nul && (echo Already installed.) || call :install Git.Git "https://git-scm.com/download/win"
where git >nul 2>nul || echo Git is not visible in this window yet. Once it is installed, use a new window for setup-git.bat.
echo.
echo === 2 of 4: Python ===
call _system\tools\find_python.cmd
if defined PY (echo Already installed: "%PY%") else (call :install Python.Python.3.12 "https://www.python.org/downloads/")
if not defined PY call _system\tools\find_python.cmd
if not defined PY (echo Python was not found. If it was just installed, close this window, open it again and re-run install-tools.bat. & goto :fail)
echo.
echo === 3 of 4: Python packages ===
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install -r requirements.txt || (echo Installing the Python packages failed. See the message above. & goto :fail)
echo.
echo === 4 of 4: Chromium for Playwright, used to print the PDFs and check the website ===
"%PY%" -m playwright install chromium || (echo Installing Chromium failed. See the message above. & goto :fail)
echo.
echo All done. Next: double-click setup-git.bat (once), then rebuild.bat whenever the data changes.
if not defined KB_NOPAUSE pause
exit /b 0

:install
if not defined WINGET (echo winget, the Windows package installer, is not available here. Install it by hand from %~2 & exit /b 1)
winget install --id %1 -e --source winget --accept-source-agreements --accept-package-agreements
exit /b

:fail
echo.
echo The installation did not finish. Fix the problem above and run install-tools.bat again.
if not defined KB_NOPAUSE pause
exit /b 1
