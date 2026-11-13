@echo off
echo ================================================
echo   Build StreamPad menjadi file .exe portable
echo ================================================
echo.

echo [0/3] Mengecek instalasi Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ================================================
    echo   Python tidak ditemukan di PATH!
    echo.
    echo   1. Download Python di https://python.org/downloads
    echo   2. Saat install, WAJIB centang "Add python.exe to PATH"
    echo   3. Restart Command Prompt / PC ini, lalu jalankan build.bat lagi
    echo ================================================
    pause
    exit /b 1
)
python --version

echo.
echo [1/3] Menginstall dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Gagal install dependencies. Cek pesan error di atas.
    pause
    exit /b 1
)

echo.
echo [2/3] Membersihkan hasil build lama (jika ada)...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del StreamPad.spec 2>nul

echo.
echo [3/3] Compile ke folder aplikasi...
python -m PyInstaller --noconfirm --clean --onedir --windowed --noupx --name StreamPad --icon=assets\icon.ico --version-file=version_info.txt --add-data "assets\icon.ico;assets" --exclude-module tkinter main.py

echo.
if exist dist\StreamPad\StreamPad.exe (
    echo BERHASIL! Jalankan: dist\StreamPad\StreamPad.exe
    echo Pindahkan SELURUH folder dist\StreamPad kalau mau dipakai di tempat lain.
) else (
    echo Build gagal. Cek pesan error di atas.
)
pause
