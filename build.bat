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
echo [3/3] Compile ke satu file .exe portable...
python -m PyInstaller --onefile --windowed --name "StreamPad-1.0.0-portable" --icon=assets\icon.ico main.py

echo.
if exist dist\StreamPad-1.0.0-portable.exe (
    echo ================================================
    echo   BERHASIL!
    echo   File ada di: dist\StreamPad-1.0.0-portable.exe
    echo   Tinggal double klik - portable, tanpa instalasi.
    echo   Data tombol tersimpan otomatis di config.json
    echo   pada folder yang sama dengan file .exe ini.
    echo ================================================
) else (
    echo Build gagal. Cek pesan error di atas.
)
pause
