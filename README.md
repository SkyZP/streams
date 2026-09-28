# StreamPad

Aplikasi soundboard & macro deck ala Stream Deck, dibuat untuk dipakai bareng
macropad **DumbPad** (QMK). Modern UI, portable (tanpa installer), dan tombol
bisa dikustomisasi penuh: putar sound effect dari file di komputer, atur
volume sistem, dan dijalankan lewat klik mouse ATAU lewat tombol fisik di
DumbPad.

## ⚠️ Catatan penting soal file .exe

Aplikasi ini dibuat sebagai **source code Python**, bukan file `.exe` yang
sudah jadi. Ini karena proses compile ke `.exe` harus dilakukan di mesin
Windows (butuh Python + PyInstaller versi Windows), sementara source code ini
disusun di lingkungan Linux tanpa akses ke toolchain Windows.

Kabar baiknya: prosesnya sudah disiapkan otomatis lewat `build.bat`. Kamu
tinggal jalankan satu file itu di PC Windows-mu, dan hasilnya adalah **file
`.exe` portable** — tinggal double klik, tanpa instalasi, tanpa registry,
persis seperti yang kamu minta.

## Cara build jadi .exe

1. Install Python 3.10+ di Windows (dari python.org), pastikan saat instalasi
   centang **"Add Python to PATH"**.
2. Extract folder `StreamPad` ini di mana saja.
3. Double klik `build.bat` (atau jalankan dari Command Prompt di folder ini).
4. Tunggu sampai selesai. Hasilnya ada di `dist\StreamPad-1.0.0-portable.exe`
   — sudah pakai ikon custom, persis seperti contoh `DLSS5-Swapper-portable.exe`
   yang kamu tunjukkan.
5. Copy file `.exe` itu ke mana pun kamu mau — bisa dipindah-pindah,
   dijalankan dari flashdisk, dari folder mana saja, tanpa instalasi.

### Soal penyimpanan data
Sama seperti aplikasi portable pada umumnya: begitu kamu jalankan
`StreamPad-1.0.0-portable.exe`, aplikasi otomatis membuat file `config.json`
**di folder yang sama** dengan file `.exe`-nya. Semua tombol, path sound
effect, dan hotkey yang kamu atur tersimpan di situ — tidak nulis ke
registry atau AppData. Kalau `.exe` dipindah, cukup bawa juga `config.json`
di sebelahnya supaya setup tombolmu ikut terbawa.

Build hanya perlu dilakukan **sekali** di komputer manapun yang akan dipakai
(atau ulangi kalau kamu edit source code-nya).

> Catatan: Windows Defender / antivirus kadang menandai file `.exe` hasil
> PyInstaller sebagai mencurigakan (false positive) karena cara PyInstaller
> mem-bundle Python — ini umum terjadi dan bukan berarti aplikasinya
> berbahaya. Kalau muncul warning, klik "More info" → "Run anyway", atau
> tambahkan exception di antivirus.

## Menjalankan tanpa build (mode development)

```
pip install -r requirements.txt
python main.py
```

## Cara pakai aplikasi

### 1. Menambah tombol
Klik **"+ Tambah Tombol"**, lalu atur:
- **Nama Tombol** — label yang tampil.
- **Aksi**:
  - *Putar Suara* — pilih file `.mp3/.wav/.ogg/.flac/.m4a` dari komputermu.
  - *Volume Naik / Turun* — atur besar step-nya (misal 5% tiap tekan).
  - *Mute / Unmute* — toggle mute sistem.
  - *Set Volume ke Level Tertentu* — langsung set ke persentase tertentu
    (misal langsung 50%).
- **Hotkey** — klik "Rekam tombol...", lalu tekan tombol di DumbPad-mu.
  Aplikasi akan otomatis mendeteksi kode tombolnya.
- **Warna** — biar gampang dibedakan secara visual.

### 2. Mengedit / menghapus tombol
Klik **"Mode Edit: OFF"** supaya berubah jadi **ON**. Selama mode ini aktif,
klik tombol mana pun di grid untuk membuka ulang konfigurasinya (termasuk
tombol "Hapus Tombol" di dalam dialog). Matikan lagi mode edit untuk kembali
ke mode normal (klik = jalankan aksi).

### 3. Integrasi dengan DumbPad
DumbPad menjalankan firmware QMK dan oleh Windows dibaca sebagai **keyboard
USB biasa**. Jadi setiap tombol fisik di DumbPad = mengirim kode tombol
tertentu, sama seperti kamu menekan huruf/angka di keyboard.

StreamPad "mendengarkan" kode tombol tersebut secara **global** (bekerja
walau window StreamPad sedang tidak aktif/di-minimize) lewat fitur *Rekam
Hotkey*. Jadi alurnya:

1. Program dulu keymap DumbPad-mu (lewat QMK Toolbox / VIA / Vial) supaya
   tiap tombol fisik mengirim kode unik. **Disarankan pakai tombol F13–F24**,
   karena rentang ini jarang dipakai aplikasi lain sehingga tidak akan
   bentrok dengan shortcut yang sudah ada.
2. Di StreamPad, buat/edit tombol → klik "Rekam tombol..." → tekan tombol
   fisik yang sesuai di DumbPad.
3. Selesai. Sekarang menekan tombol fisik itu di DumbPad akan menjalankan
   aksi yang sama seperti mengklik tombolnya di layar.

### 4. Konfigurasi tersimpan otomatis
Semua tombol yang kamu buat disimpan di file `config.json`, ada di folder
yang sama dengan `StreamPad.exe`. File ini ikut portable — kalau kamu pindah
`StreamPad.exe` ke folder/komputer lain, bawa juga `config.json`-nya supaya
setup tombolmu tidak hilang.

## Catatan teknis

- Pendengaran hotkey global memakai library `keyboard`, yang di beberapa
  sistem **butuh dijalankan sebagai Administrator** agar bisa mendeteksi
  tombol walau aplikasi lain sedang fokus. Kalau hotkey dari DumbPad tidak
  terdeteksi, coba klik kanan `StreamPad.exe` → "Run as administrator".
- Kontrol volume sistem memakai `pycaw` (Windows Core Audio API) — hanya
  berjalan di Windows.
- Pemutaran suara memakai `QtMultimedia` (bawaan PySide6) sehingga mendukung
  beberapa suara diputar bersamaan (overlap), seperti soundboard sungguhan.

## Struktur project

```
StreamPad/
├── main.py                  # entry point
├── modules/
│   ├── gui.py                # UI utama + dialog konfigurasi tombol
│   ├── audio_manager.py      # pemutaran sound effect
│   ├── volume_manager.py     # kontrol volume sistem (pycaw)
│   ├── hotkey_manager.py     # pendengaran hotkey global (termasuk DumbPad)
│   ├── config_manager.py     # simpan/muat config.json
│   └── styles.py              # tema modern (dark)
├── requirements.txt
├── build.bat                  # compile otomatis jadi .exe portable
└── README.md
```
