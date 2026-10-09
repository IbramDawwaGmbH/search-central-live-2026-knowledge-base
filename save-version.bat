@echo off
rem Saves the current state of the folder as a new version in git (double-click it).
rem A privacy check stops before anything that looks like a photo, recording or transcript is saved.
setlocal
cd /d "%~dp0"
set "SAVED="
set "TAGGED="
set "MSGFILE=%TEMP%\kb-version-message-%RANDOM%%RANDOM%.txt"
where git >nul 2>nul || (echo Git is not installed. Run install-tools.bat first. & goto :fail)
if not exist .git (echo This folder is not a git repository yet. Run setup-git.bat first. & goto :fail)
git rev-parse -q --verify HEAD >nul 2>nul || (echo There is no first version yet. Run setup-git.bat first. & goto :fail)
call _system\tools\find_python.cmd
if not defined PY (echo Python was not found, so the privacy check cannot run. Run install-tools.bat first. & goto :fail)

echo Changes since the last version:
git status --short -uall
echo.
set "CHANGES="
for /f "delims=" %%i in ('git status --porcelain -uall') do set "CHANGES=1"
if not defined CHANGES (echo Nothing has changed since the last version. & goto :tag)

set "MSG="
set /p "MSG=Describe this version in a few words: "
if not defined MSG set "MSG=Update"
echo.
"%PY%" _system\tools\check_commit.py
if errorlevel 3 goto :confirm
if errorlevel 1 (echo The privacy check did not run correctly. & goto :fail)
goto :save

:confirm
set "OK="
set /p "OK=Type YES to save these files anyway, or press Enter to stop: "
if defined OK set "OK=%OK:"=%"
if /i not "%OK%"=="YES" (echo Stopped at your request. & goto :fail)

:save
"%PY%" -c "import os,sys; open(sys.argv[1],'w',encoding='utf-8',newline='\n').write((os.environ['MSG'].strip() or 'Update')+'\n')" "%MSGFILE%" || (echo Could not write the version description. & goto :fail)
call _system\tools\git_identity.cmd || goto :fail
git add -A || (echo git add failed. See the message above. & goto :fail)
git diff --cached --quiet && (echo Nothing to save: git found no real changes. & goto :tag)
git commit -q -F "%MSGFILE%" || (echo The commit failed. See the message above. & goto :fail)
set "SAVED=1"
echo Saved a new version:
git log --oneline -1

:tag
echo.
set "TAG="
set /p "TAG=Version tag (for example v2.0.0), or press Enter to skip: "
if defined TAG set "TAG=%TAG:"=%"
if not defined TAG goto :done
"%PY%" -c "import os,re,sys; sys.exit(0 if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,40}', os.environ['TAG'].strip()) else 1)" || (echo That is not a valid tag name: use letters, digits, dots and dashes, like v2.0.0. & goto :fail)
for /f "tokens=1" %%t in ("%TAG%") do set "TAG=%%t"
git check-ref-format "refs/tags/%TAG%" || (echo That is not a valid tag name. & goto :fail)
git rev-parse -q --verify "refs/tags/%TAG%" >nul && (echo The tag %TAG% already exists. Pick a new one. & goto :fail)
call _system\tools\git_identity.cmd || goto :fail
if defined SAVED (git tag -a "%TAG%" -F "%MSGFILE%") else (git tag -a "%TAG%" -m "Version %TAG%")
if errorlevel 1 (echo Tagging failed. See the message above. & goto :fail)
set "TAGGED=1"

:done
echo.
git log --oneline --decorate -5
echo.
if defined SAVED if defined TAGGED echo Done. The new version is saved and tagged %TAG%.
if defined SAVED if not defined TAGGED echo Done. The new version is saved.
if not defined SAVED if defined TAGGED echo Done. Nothing had changed; the current version is now tagged %TAG%.
if not defined SAVED if not defined TAGGED echo Nothing had changed, so no new version was saved.
call :cleanup
if not defined KB_NOPAUSE pause
exit /b 0

:fail
echo.
if defined SAVED (echo The new version WAS saved, but the step above failed.) else (echo Nothing was saved.)
call :cleanup
if not defined KB_NOPAUSE pause
exit /b 1

:cleanup
if exist "%MSGFILE%" del "%MSGFILE%" >nul 2>nul
exit /b 0
