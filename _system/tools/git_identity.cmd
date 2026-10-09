@echo off
rem Makes sure git knows who saves versions. Asks once and stores the answer in this repository only.
rem Usage (from the repository folder): call _system\tools\git_identity.cmd || goto :fail
set "KB_NAME="
set "KB_MAIL="
for /f "delims=" %%i in ('git config user.name 2^>nul') do set "KB_NAME=%%i"
for /f "delims=" %%i in ('git config user.email 2^>nul') do set "KB_MAIL=%%i"
if defined KB_NAME if defined KB_MAIL goto :ok
echo.
echo Git records a name and an e-mail address with every version you save.
echo They stay in this folder's history. If you might ever publish the repository,
echo use your GitHub "noreply" address rather than your personal e-mail.
if not defined KB_NAME set /p "KB_NAME=Your name: "
if not defined KB_MAIL set /p "KB_MAIL=Your e-mail address: "
if defined KB_NAME set "KB_NAME=%KB_NAME:"=%"
if defined KB_MAIL set "KB_MAIL=%KB_MAIL:"=%"
if not defined KB_NAME goto :missing
if not defined KB_MAIL goto :missing
git config user.name "%KB_NAME%" || goto :missing
git config user.email "%KB_MAIL%" || goto :missing
echo Stored for this folder only: "%KB_NAME%" "%KB_MAIL%"
:ok
set "KB_NAME="
set "KB_MAIL="
exit /b 0
:missing
set "KB_NAME="
set "KB_MAIL="
echo A name and an e-mail address are both needed to save a version.
exit /b 1
