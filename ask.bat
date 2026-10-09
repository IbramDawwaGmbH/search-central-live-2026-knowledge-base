@echo off
rem Ask the knowledge base a question. Double-click, type a question (or a thing such as 429, GSC, hreflang, or a claim id
rem such as D1-C108) and read the best matching thing and the top claims, each with its citation. Empty line to quit.
rem Offline and read-only: the answers come only from 60-outputs\agent-pack (rebuild.bat writes it); nothing is sent anywhere.
rem From a terminal:  ask.bat what does Google say about 429?   answers that question first, then keeps asking.
rem AI agents call the same thing directly:  python _system\kb_query.py search "..."  (see 60-outputs\agent-pack\AGENTS.md).
setlocal
cd /d "%~dp0"
title Deep Dive: ask the knowledge base
rem UTF-8 for names such as Soren Bendig with their accents; the console's code page is put back at the end.
set "OLDCP="
for /f "tokens=2 delims=:" %%c in ('chcp') do set "OLDCP=%%c"
if defined OLDCP set "OLDCP=%OLDCP: =%"
if defined OLDCP set "OLDCP=%OLDCP:.=%"
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
call "%~dp0_system\tools\find_python.cmd"
if not defined PY (echo Python was not found. Run install-tools.bat first. & set "RC=1" & goto :end)
if not exist "%~dp060-outputs\agent-pack\claims.jsonl" (echo The agent pack is missing. Run rebuild.bat first. & set "RC=1" & goto :end)
"%PY%" "%~dp0_system\kb_query.py" ask %*
set "RC=%ERRORLEVEL%"
:end
if defined OLDCP chcp %OLDCP% >nul
if not "%RC%"=="0" pause
exit /b %RC%
