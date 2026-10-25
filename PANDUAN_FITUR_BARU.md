# Panduan Fitur Baru — SMILE Dashboard

Dokumen ini menjelaskan semua fitur yang baru ditambahkan: role **Orang Tua**,
**Absensi**, **Tugas & Nilai**, **Ranking**, dan **Pembayaran SPP**.

## 1. Menjalankan Project

Tidak ada langkah tambahan dari biasanya:

```bash
pip install -r requirements.txt --break-system-packages   # atau tanpa flag ini kalau pakai venv
python manage.py migrate
python manage.py runserver
```

Migration baru (kelas 1A–6B, dsb) otomatis jalan lewat `migrate` seperti biasa.

## 2. Akun Demo (contoh data siap pakai)

Supaya langsung bisa dicoba, sudah dibuatkan data contoh lewat perintah
`python manage.py seed_demo` (sudah dijalankan sekali, jadi datanya sudah ada
di `db.sqlite3` yang dikirim). Semua akun demo pakai password **`demo12345`**:

| Username | Role | Keterangan |
|---|---|---|
| `demo_guru1` | Guru | Wali kelas 4A & 4B, buat 2 tugas di tiap kelas |
| `demo_andi`, `demo_bunga`, `demo_citra`, `demo_dani` | Murid | Kelas 4A |
| `demo_eka`, `demo_fajar`, `demo_gita` | Murid | Kelas 4B |
| `demo_ortu1` | Orang Tua | Anak: Andi (4A) & Eka (4B) — coba fitur ganti-anak |

Status SPP bulan berjalan sengaja dibuat bervariasi:
- **Lunas**: Andi, Dani, Gita
- **Dibayar Sebagian**: Bunga & Eka (bayar Rp200.000 dari tagihan Rp300.000 → sisa Rp100.000, persis skenario yang diminta)
- **Belum Bayar**: Citra, Fajar

Akun lama (`admin1234`, `Fadilganteng`, `pasyah`) **tidak diubah/disentuh** oleh seed ini.

**Sebelum dipakai sekolah sungguhan**, hapus semua data demo dengan:
```bash
python manage.py flush_demo
```
Ini hanya menghapus user berawalan `demo_` beserta data turunannya (siswa, nilai,
absensi, tagihan, dst). Aman dijalankan kapan saja.

## 3. Role Orang Tua

Role baru `orang_tua` ditambahkan di `accounts.Profile`. Alurnya:

1. Admin membuat **User** baru lewat Django Admin (`/admin/auth/user/`)
2. Admin membuat **Profile** untuk user itu dengan role `Orang Tua` (`/admin/accounts/profile/`)
3. Admin membuat **OrangTua** (`/admin/akademik/orangtua/`), pilih `user` tadi, lalu di field **anak** pilih satu atau lebih **Siswa** (bisa lebih dari satu kalau kakak-adik satu sekolah)

Setelah itu orang tua bisa login seperti biasa lewat halaman login utama, dan
otomatis diarahkan ke dashboard khusus orang tua (`/dashboard/orangtua/`).

Kalau anaknya lebih dari satu, ada tombol ganti-anak di sidebar/dashboard
(pakai `?anak=<id>` di URL) untuk pindah lihat data anak yang mana.

## 4. Kelas (sekarang ada rombel, bukan cuma angka 1–6)

Model baru `akademik.Kelas` punya dua field penting:
- `nama` — bebas, misal **"4A"**, **"4B"**, atau nama lain (sudah di-seed otomatis 1A–6B)
- `tingkat` — angka 1–6, dipakai khusus untuk mengelompokkan **ranking paralel**
  (semua kelas tingkat yang sama, apapun nama rombelnya)

Kelola lewat `/admin/akademik/kelas/`. Field `nominal_spp` di tiap kelas
menentukan besar tagihan SPP bulanan untuk siswa di kelas itu (default Rp300.000,
bisa beda-beda per kelas).

**Catatan:** fitur "Materi" (bahan ajar) yang sudah ada sebelumnya sengaja
TIDAK diubah — materi tetap per tingkat (1–6), karena biasanya bahan ajar sama
untuk semua rombel di tingkat yang sama. Yang baru (Absensi, Tugas, Ranking)
memakai kelas/rombel yang sebenarnya (4A vs 4B dibedakan).

## 5. Menambahkan Siswa ke Kelas

Lewat `/admin/akademik/siswa/`: buat/pilih User (role Murid), lalu pilih
**kelas**-nya dari dropdown. Siswa lama (`pasyah`) otomatis sudah ditautkan ke
kelas 1A supaya tidak error — silakan pindahkan ke kelas yang benar.

## 6. Absensi

- **Guru** → sidebar "Absensi Murid" → pilih kelas → pilih tanggal → tandai
  tiap siswa Hadir/Izin/Sakit/Alpa → Simpan. Mengisi ulang di tanggal yang
  sama akan **meng-update**, bukan membuat data dobel.
- Ada rekap otomatis (total & persentase kehadiran) di bawah form.
- **Murid** & **Orang Tua** bisa lihat riwayat + ringkasan kehadiran (read-only).

## 7. Tugas & Nilai

- **Guru** → sidebar "Tugas & Nilai" → buat tugas baru (judul bebas, misal
  "Tugas 1"), pilih kelas, mapel, dan **jenis**: *Tulis di Buku* atau *Online*.
- Klik "Input Nilai" pada tugas untuk mengisi nilai (0–100) tiap siswa di
  kelas itu. Nilai di luar rentang otomatis dipotong ke 0–100.
- Guru hanya bisa mengedit/menilai tugas buatannya sendiri (admin bisa semua).
- **Murid** & **Orang Tua** bisa lihat semua nilai + rata-rata (read-only).

## 8. Ranking

Rumus (di `akademik/ranking.py`):

```
Skor = 70% x rata-rata nilai tugas + 30% x persentase kehadiran
```

- **Ranking Kelas**: dibandingkan hanya dengan teman sekelas (mis. sesama 4A).
- **Ranking Paralel**: dibandingkan dengan semua siswa di tingkat yang sama
  lintas kelas (4A + 4B + ... digabung).
- Siswa yang belum punya data absensi sama sekali dianggap 100% hadir dulu
  (tidak dirugikan), bukan 0%.
- Bobot 70/30 ini konstanta di bagian atas `akademik/ranking.py`
  (`BOBOT_NILAI`, `BOBOT_KEHADIRAN`) — gampang diubah kalau mau proporsi lain.
- Guru & Admin bisa lihat ranking kelas manapun. Murid & Orang Tua otomatis
  melihat ranking kelasnya/anaknya sendiri, dengan barisnya sendiri
  di-highlight.

## 9. Pembayaran SPP

Alur (diatur admin, sesuai permintaan):

1. Admin atur **Rekening Bank** (dummy) di halaman "Pembayaran SPP" — ini yang
   ditampilkan ke murid/orang tua sebagai tujuan transfer.
2. Admin klik **"Generate Tagihan SPP"** untuk bulan tertentu → sistem
   otomatis membuat tagihan untuk semua siswa aktif sesuai nominal SPP
   kelasnya masing-masing. Siswa yang sudah punya tagihan bulan itu dilewati
   (tidak dobel).
3. Admin **"Catat Pembayaran"** tiap kali ada transfer masuk (jumlah, tanggal,
   catatan opsional). Satu tagihan boleh dicatat beberapa kali pembayaran
   (dicicil).
4. Status otomatis terhitung:
   - **Belum Bayar** — belum ada pembayaran sama sekali
   - **Dibayar Sebagian** — sudah bayar tapi belum lunas (sisa ditampilkan)
   - **Lunas** — total pembayaran ≥ nominal tagihan

   Contoh persis dari permintaan: SPP Rp300.000, bayar Rp200.000 → status
   "Dibayar Sebagian", sisa Rp100.000. Begitu dilunasi, otomatis jadi "Lunas".

Pembayaran murni dicatat manual oleh admin (belum ada integrasi payment
gateway/bank sungguhan) — sesuai permintaan "nomor bank dummy dulu".

Murid & Orang Tua hanya bisa **melihat** status tagihan + nomor rekening
(read-only), tidak bisa mengubah apapun.

## 10. Hal Lain yang Ikut Diperbaiki/Ditambahkan

- **Jazzmin** (tema Django Admin yang lebih modern) diaktifkan — sudah ada di
  `requirements.txt` sebelumnya tapi belum pernah dipasang di `settings.py`.
  Banyak pengelolaan data master (siswa, orang tua, kelas, dll) memang paling
  nyaman lewat Django Admin ini.
- `PyJWT` ditambahkan ke `requirements.txt` — sebelumnya dipakai di
  `portal/views.py` (untuk SSO ke Quiz app) tapi tidak tercantum, jadi
  instalasi baru dari nol akan gagal tanpa ini.
- Bug lama di `kelola_materi.html`: halaman bisa error kalau ada materi yang
  dibuat tanpa file terlampir. Sudah diberi pengaman yang sama seperti di
  `daftar_materi.html`.
- Semua role sekarang dijaga konsisten: murid yang coba buka dashboard guru
  (atau sebaliknya) otomatis diarahkan balik ke dashboard masing-masing.
- Notifikasi sukses/error (misal "Absensi berhasil disimpan") sekarang muncul
  di semua halaman lewat Django messages framework.

## 11. Testing

Ada test otomatis di `akademik/tests.py`, `pembayaran/tests.py`, dan
`portal/tests.py` (33 test, mencakup akses per-role, absensi, tugas/nilai,
perhitungan ranking, dan status pembayaran SPP). Jalankan dengan:

```bash
python manage.py test
```
