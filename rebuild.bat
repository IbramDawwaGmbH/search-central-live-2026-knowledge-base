@echo off
rem Rebuilds topic pages, session pages, maps and the agent pack, then the PDFs, then the website.
rem Usage: double-click (the PDF of every day that has a template), or  rebuild.bat day2  (that day's PDF only).
rem Only the Deep Dive edition (style ocean, the main edition) is rebuilt. The classic Art Deco and modern PDFs are frozen
rem at their v2.4.0 content and are never rewritten here: 60-outputs\pdf\classic-editions-log.md lists what they lack.
rem To build a classic edition by hand (this replaces the frozen file with today's content; then update the log):
rem   python _system\pdf\make_pdf.py day2 deco      (Art Deco)
rem   python _system\pdf\make_pdf.py day2 modern    (modern)
rem and run this file again so the web edition copies the new PDF. Each day is built separately; the summary says what failed.
setlocal
cd /d "%~dp0"
set "DAY=%~1"
set "R_KB=not run"
set "R_SITE=not run"
set "R_PDF=not run"
set "PDF_OK="
set "PDF_BAD="
set "FAILED="
call _system\tools\find_python.cmd
if not defined PY (echo Python was not found. Run install-tools.bat first. & set "FAILED=1" & goto :summary)
echo Using Python: "%PY%"

echo.
echo === 1 of 3: knowledge base (topics, sessions, maps, agent pack) ===
"%PY%" _system\build_kb.py
if errorlevel 1 (set "R_KB=FAILED" & set "FAILED=1" & set "R_SITE=skipped (the knowledge base build failed)" & set "R_PDF=skipped (the knowledge base build failed)" & goto :summary)
set "R_KB=ok"

echo.
echo === 2 of 3: PDFs (Deep Dive edition; the classic editions stay frozen) ===
if defined DAY (call :pdf "%DAY%" strict) else (for %%f in (_system\pdf\day*.template.html) do for /f "delims=." %%d in ("%%~nf") do call :pdf "%%d")
if defined PDF_BAD (set "R_PDF=FAILED for%PDF_BAD%" & set "FAILED=1")
if defined PDF_BAD if defined PDF_OK set "R_PDF=%R_PDF%; ok:%PDF_OK%"
if defined PDF_BAD goto :site
if defined PDF_OK (set "R_PDF=ok:%PDF_OK%") else (set "R_PDF=no day template found in _system\pdf" & set "FAILED=1")

:site
rem The website lists the PDFs (and their sizes) that exist when it is built, so it comes after them.
echo.
echo === 3 of 3: website ===
if not exist _system\site\build_site.py (set "R_SITE=skipped (_system\site\build_site.py does not exist yet)" & goto :summary)
"%PY%" _system\site\build_site.py
if errorlevel 1 (set "R_SITE=FAILED" & set "FAILED=1") else (set "R_SITE=ok")

:summary
echo.
echo ================= Summary =================
echo   Knowledge base: %R_KB%
echo   PDFs:           %R_PDF%
echo                   (Deep Dive only; Art Deco and modern stay frozen at v2.4.0)
echo   Website:        %R_SITE%
echo ===========================================
if not defined FAILED goto :allok
echo Something failed: read the messages above. Do not save a version until rebuild.bat runs cleanly.
if defined PDF_BAD echo A PDF that is open in a viewer cannot be rewritten: close it and run rebuild.bat again.
if not defined KB_NOPAUSE pause
exit /b 1

:allok
echo Everything was rebuilt. The Deep Dive PDFs are in 60-outputs\pdf, the website is 60-outputs\site\index.html, the map is 50-maps\mindmap.html.
if not defined KB_NOPAUSE pause
exit /b 0

:pdf
echo "%~1"| findstr /r /x /i /c:"\"day[0-9][0-9]*\"" >nul || goto :pdfname
call :pdfstyle %~1 ocean
exit /b 0

:pdfstyle
echo --- %1, %2 style ---
"%PY%" _system\pdf\make_pdf.py %1 %2
if errorlevel 1 (set "PDF_BAD=%PDF_BAD% %1-%2") else (set "PDF_OK=%PDF_OK% %1-%2")
exit /b 0

:pdfname
echo Skipping "%~1": not a day name like day2.
if "%~2"=="strict" set "PDF_BAD=%PDF_BAD% [not a day name]"
exit /b 0
