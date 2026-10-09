@echo off
rem Run once: turns this folder into a git repository and saves the first version, tagged with the
rem newest version in CHANGELOG.md (v1.0.0 if there is none). Private folders stay out (.gitignore).
setlocal
cd /d "%~dp0"
where git >nul 2>nul || (echo Git is not installed. Run install-tools.bat first, or get it from https://git-scm.com/download/win & goto :fail)
if not exist .git goto :init
git rev-parse -q --verify HEAD >nul 2>nul && (echo This folder already has a version history. Use save-version.bat to save new versions. & goto :end)
echo This folder is a git repository, but no version is saved in it yet. Continuing.
goto :ready

:init
git init -q -b main || (echo git init failed. See the message above. & goto :fail)

:ready
git config core.autocrlf false
call _system\tools\git_identity.cmd || goto :fail
set "VER="
if exist CHANGELOG.md for /f "tokens=2" %%v in ('findstr /b /r /c:"## v[0-9]" CHANGELOG.md') do if not defined VER set "VER=%%v"
if not defined VER set "VER=v1.0.0"
echo "%VER%"| findstr /r /x /c:"\"v[0-9][0-9.]*\"" >nul || set "VER=v1.0.0"
echo.
call _system\tools\find_python.cmd
if not defined PY goto :noguard
"%PY%" _system\tools\check_commit.py
if errorlevel 3 goto :confirm
if errorlevel 1 (echo The privacy check did not run correctly. & goto :fail)
goto :commit

:noguard
echo Python was not found, so the automatic privacy check cannot run. These files would be saved:
git add -A --dry-run
echo Check that no photo, recording or transcript is in the list (raw files belong in 00-raw\).

:confirm
set "OK="
set /p "OK=Type YES to save these files, or press Enter to stop: "
if defined OK set "OK=%OK:"=%"
if /i not "%OK%"=="YES" (echo Stopped at your request. & goto :fail)

:commit
git add -A || (echo git add failed. See the message above. & goto :fail)
git diff --cached --quiet && (echo There is nothing to save in this folder. & goto :fail)
git commit -q -m "Knowledge base %VER%: first version in git" || (echo The commit failed. See the message above. & goto :fail)
git tag -a "%VER%" -m "%VER%: first version in git" || (echo The first version was saved, but tagging it %VER% failed. & goto :fail)
echo.
git log --oneline --decorate -1
echo.
echo Done. Version %VER% is saved. Private folders are left out by .gitignore.
goto :end

:fail
echo.
echo Setup did not finish. Fix the problem above and run setup-git.bat again.
if not defined KB_NOPAUSE pause
exit /b 1

:end
if not defined KB_NOPAUSE pause
exit /b 0
