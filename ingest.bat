@echo off
rem Drag a folder of event material (slide photos, videos, recordings, transcripts) onto this file,
rem or double-click it and drag the folder into the window. It asks for the day, shows what it would do,
rem and after you confirm it copies the files UNTOUCHED into 00-raw\dayN\ (private), makes JPEG previews in
rem 10-sources\dayN\slides-jpg\ and writes 10-sources\dayN\media.yaml with capture times and suggested sessions.
rem The source folder is only read. Files already imported are skipped, so running it twice is safe.
rem Exit code: 0 done, 1 nothing imported or some files need a look, 2 the import stopped part way.
setlocal
cd /d "%~dp0"
call _system\tools\find_python.cmd
if not defined PY (echo Python was not found. Run install-tools.bat first. & goto :fail)
set "ARGS="
:args
if "%~1"=="" goto :argsdone
rem A path ending in a backslash (a drive root such as E:\) would escape the closing quote: end it with a dot instead.
set "A=%~1"
if "%A:~-1%"=="\" set "A=%A%."
set ARGS=%ARGS% "%A%"
shift
goto :args
:argsdone
set "A="
if defined ARGS goto :day
set "SRC="
echo Drag the folder with the new material into this window, then press Enter.
set /p "SRC=Folder: "
if defined SRC set "SRC=%SRC:"=%"
if not defined SRC (echo No folder was given. & goto :fail)
if "%SRC:~-1%"=="\" set "SRC=%SRC%."
set ARGS="%SRC%"

:day
set "DAY="
set /p "DAY=Which day of the event is this material from? Type the number, for example 2: "
if defined DAY set "DAY=%DAY:"=%"
if not defined DAY (echo No day was given. & goto :fail)
echo "%DAY%"| findstr /r /x /c:"\" *[1-9][0-9]* *\"" >nul || (echo Please type only a day number, for example 2. & goto :fail)
for /f "tokens=1" %%d in ("%DAY%") do set "DAY=%%d"
echo.
echo Checking what would be copied. Nothing is changed yet.
echo.
"%PY%" _system\tools\ingest.py %ARGS% --day %DAY% --dry-run
if errorlevel 2 goto :fail
if errorlevel 1 (echo. & echo Some files have problems, listed above. They will be skipped; the others can be copied.)
echo.
set "OK="
set /p "OK=Copy these files into 00-raw\day%DAY% now? Type Y and press Enter: "
if defined OK set "OK=%OK:"=%"
if /i "%OK%"=="Y" goto :copy
if /i "%OK%"=="YES" goto :copy
echo Nothing was copied.
goto :end

:copy
echo.
"%PY%" _system\tools\ingest.py %ARGS% --day %DAY%
if errorlevel 2 goto :stopped
if errorlevel 1 goto :problems
echo.
echo Done. The files are in 00-raw\day%DAY% and the index is 10-sources\day%DAY%\media.yaml.
goto :end

:problems
echo.
echo Finished, but some files need a look: see the problems listed above.
echo A file marked NAME CLASH was NOT copied: rename it and run ingest.bat again.
echo A file marked COPY FAILED was NOT copied: close the program that uses it (or copy it off the card first) and run ingest.bat again.
if not defined KB_NOPAUSE pause
exit /b 1

:stopped
echo.
echo The import STOPPED part way: see the message above. Files reported as copied are in 00-raw\day%DAY%;
echo the index 10-sources\day%DAY%\media.yaml may be out of date. Fix the problem and run ingest.bat again
echo with the same folder: files already copied are skipped.
if not defined KB_NOPAUSE pause
exit /b 2

:fail
echo.
echo Nothing was imported.
if not defined KB_NOPAUSE pause
exit /b 1

:end
if not defined KB_NOPAUSE pause
exit /b 0
