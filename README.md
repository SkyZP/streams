# StreamPad

Aplikasi soundboard & macro deck ala Stream Deck, dibuat untuk dipakai bareng
macropad **DumbPad** (QMK). Tampilan **kaca bening monokrom**: background
hitam-putih blur, panel & tombol transparan, toggle yang meluncur halus, dan
dialog fade-in. Pengaturan (⚙) berisi jumlah kolom, volume utama, Simpan,
**Export / Import config.json**, dan Kelola Profile.
Portable (tanpa installer). Setiap tombol punya dua
pilihan aksi saja — **Putar Suara** atau **Buka Aplikasi** — biar tetap
simpel dan gampang dikombinasikan dengan software lain yang sudah kamu
pakai.

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
4. Tunggu sampai selesai. Hasilnya ada di folder `dist\StreamPad\`
   (jalankan `StreamPad.exe` di dalamnya). Format folder (bukan satu file)
   dipakai supaya jauh lebih jarang dianggap virus oleh antivirus.
5. Copy **seluruh folder** `StreamPad` itu ke mana pun kamu mau (flashdisk,
   dll) — tanpa instalasi. Jangan jalankan dari dalam file .zip.

### Soal penyimpanan data
Sama seperti aplikasi portable pada umumnya: begitu kamu jalankan
`StreamPad.exe`, aplikasi otomatis membuat file `config.json`
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
Klik **"＋ Tambah Tombol"**, lalu atur:
- **Nama Tombol** — label yang tampil.
- **Aksi**:
  - *Putar Suara* — pilih file `.mp3/.wav/.ogg/.flac/.m4a` dari komputermu,
    atur volume khusus suara ini, dan **potong durasinya** kalau file
    aslinya kepanjangan: geser slider "Mulai" & "Selesai" untuk menentukan
    bagian yang mau diputar, lalu klik "▶ Preview Potongan" buat dengar
    hasilnya sebelum disimpan.
  - *Buka Aplikasi* — pilih file `.exe` (atau file apa pun) yang mau
    dijalankan, dengan argumen opsional kalau perlu.
- **Hotkey** — klik tombol rekam, lalu tekan tombol di DumbPad-mu.
  Aplikasi akan otomatis mendeteksi kode tombolnya.
- **Warna** — biar gampang dibedakan secara visual, sekaligus jadi warna
  efek glow saat kartu tombol di-hover.

### 2. Mengedit / menghapus tombol
Klik toggle **"✎ Edit"** di kanan atas. Selama mode ini aktif, klik kartu
tombol mana pun untuk membuka ulang konfigurasinya (termasuk tombol "Hapus
Tombol" di dalam dialog). Pindah lagi ke **"▶ Jalankan"** untuk kembali ke
mode normal (klik = jalankan aksi).

### 3. Profile (banyak set tombol)
Di bawah header ada bar profile. Klik nama profile untuk pindah set tombol,
klik **"＋ Profile"** untuk bikin profile baru (kosong), atau klik **"⚙"**
untuk mengubah nama / menghapus profile yang sudah ada. Berguna kalau kamu
mau, misalnya, satu profile untuk sound effect meme dan profile lain untuk
shortcut aplikasi kerja — tinggal pencet tombol di DumbPad untuk pindah
(atau klik nama profile-nya).

### 4. Integrasi dengan DumbPad
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

### 5. Konfigurasi tersimpan otomatis
Semua tombol yang kamu buat disimpan di file `config.json`, ada di folder
yang sama dengan `StreamPad.exe`. File ini ikut portable — kalau kamu pindah
`StreamPad.exe` ke folder/komputer lain, bawa juga `config.json`-nya supaya
setup tombolmu tidak hilang.

## Catatan teknis

- Hotkey global memakai API resmi Windows `RegisterHotKey` (bukan library
  `keyboard`), jadi tidak butuh Administrator dan tidak memicu antivirus.
  Tombol yang jadi hotkey tidak diteruskan ke aplikasi lain selama StreamPad
  berjalan; pakai F13-F24 di DumbPad supaya tidak bentrok. Klik "Rekam
  tombol" lalu tekan tombolnya (Esc untuk batal).
- Kontrol volume sistem sudah tidak ada di versi ini (dulu memakai `pycaw`);
  aksi sekarang cuma Putar Suara & Buka Aplikasi, jadi dependency-nya lebih
  ringan dan cepat di-build.
- Pemutaran suara memakai `QtMultimedia` (bawaan PySide6) sehingga mendukung
  beberapa suara diputar bersamaan (overlap), seperti soundboard sungguhan.

## Struktur project

```
StreamPad/
├── main.py                  # entry point
├── modules/
│   ├── glass.py              # komponen Liquid Glass (background, panel, tombol, toggle)
│   ├── gui.py                # layout aplikasi + dialog konfigurasi tombol & profile
│   ├── audio_manager.py      # pemutaran sound effect
│   ├── hotkey_manager.py     # pendengaran hotkey global (termasuk DumbPad)
│   ├── config_manager.py     # simpan/muat config.json
│   └── styles.py              # tema modern (dark)
├── requirements.txt
├── build.bat                  # compile otomatis jadi .exe portable
└── README.md
```
