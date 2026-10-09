@echo off
rem Sets PY to a working Python 3 (python.exe), or leaves PY undefined. Usage: call _system\tools\find_python.cmd
rem Order: every "where python" hit that really runs (skips the Microsoft Store stub), the py launcher, then the
rem per-user python.org installs. Set KB_PYTHON to force a particular python.exe.
set "PY="
set "KB_PROBE=import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)"
if defined KB_PYTHON if exist "%KB_PYTHON%" "%KB_PYTHON%" -c "%KB_PROBE%" >nul 2>nul && set "PY=%KB_PYTHON%"
if not defined PY for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY "%%i" -c "%KB_PROBE%" >nul 2>nul && set "PY=%%i"
if not defined PY for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined PY if exist "%%i" "%%i" -c "%KB_PROBE%" >nul 2>nul && set "PY=%%i"
if not defined PY for %%v in (314 313 312 311 310) do if not defined PY if exist "%LocalAppData%\Programs\Python\Python%%v\python.exe" "%LocalAppData%\Programs\Python\Python%%v\python.exe" -c "%KB_PROBE%" >nul 2>nul && set "PY=%LocalAppData%\Programs\Python\Python%%v\python.exe"
set "KB_PROBE="
if defined PY exit /b 0
exit /b 1
