@echo off
rem Builds TuringScreen.exe on Windows.
rem Requirements: Python 3.11 (py launcher) and git.
cd /d "%~dp0"
if not exist upstream git clone https://github.com/mathoudebine/turing-smart-screen-python upstream
cd upstream
git checkout 2b33ab4f00a096916dd6a1174441a53a7ec33b03
rem our files on top of the original program
xcopy /E /Y /I ..\src . >nul
rem trimmed resources for the exe (only the fonts and the theme it uses)
if exist build_res rmdir /S /Q build_res
mkdir build_res\res\themes build_res\res\fonts
copy /Y res\themes\default.yaml build_res\res\themes\ >nul
xcopy /E /I /Y res\themes\Grid3_2SSD build_res\res\themes\Grid3_2SSD >nul
for %%f in (geforce roboto roboto-mono oswald) do xcopy /E /I /Y res\fonts\%%f build_res\res\fonts\%%f >nul
xcopy /E /I /Y res\icons build_res\res\icons >nul
py -3.11 -m pip install -r requirements.txt
py -3.11 -m PyInstaller --noconfirm TuringScreen.spec
echo.
echo Result: upstream\dist\TuringScreen\TuringScreen.exe
pause
