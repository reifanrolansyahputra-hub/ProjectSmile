import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from akademik.models import Absensi, Kelas, NilaiTugas, OrangTua, Siswa, Tugas
from pembayaran.models import PembayaranSPP, RekeningBank, TagihanSPP

DEMO_PASSWORD = 'demo12345'


class Command(BaseCommand):
    help = (
        "Mengisi data contoh (demo) untuk mencoba fitur baru: siswa kelas 4A/4B, "
        "guru wali kelas, orang tua dengan 2 anak, absensi, nilai tugas, dan "
        "tagihan SPP dalam 3 status (lunas, dibayar sebagian, belum bayar). "
        "Aman dijalankan berkali-kali -- tidak akan membuat data dobel, dan "
        "tidak menyentuh akun yang sudah ada sebelumnya."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        hari_ini = timezone.localdate()

        # ---------- Guru wali kelas demo ----------
        guru, _ = self._buat_user('demo_guru1', 'guru', 'Siti', 'Guru')
        kelas_4a = Kelas.objects.get(nama='4A')
        kelas_4b = Kelas.objects.get(nama='4B')
        kelas_4a.wali_kelas = guru
        kelas_4b.wali_kelas = guru
        kelas_4a.nominal_spp = 300000
        kelas_4b.nominal_spp = 300000
        kelas_4a.save()
        kelas_4b.save()

        # ---------- Siswa ----------
        roster = [
            ('demo_andi', 'Andi', 'Pratama', kelas_4a),
            ('demo_bunga', 'Bunga', 'Lestari', kelas_4a),
            ('demo_citra', 'Citra', 'Dewi', kelas_4a),
            ('demo_dani', 'Dani', 'Saputra', kelas_4a),
            ('demo_eka', 'Eka', 'Wijaya', kelas_4b),
            ('demo_fajar', 'Fajar', 'Nugroho', kelas_4b),
            ('demo_gita', 'Gita', 'Permata', kelas_4b),
        ]
        siswa_map = {}
        for username, nama_depan, nama_belakang, kelas in roster:
            user, _ = self._buat_user(username, 'murid', nama_depan, nama_belakang)
            siswa, _ = Siswa.objects.get_or_create(user=user, defaults={'kelas': kelas})
            if siswa.kelas_id != kelas.id:
                siswa.kelas = kelas
                siswa.save()
            siswa_map[username] = siswa

        # ---------- Orang tua (Andi & Eka digambarkan kakak-adik beda kelas) ----------
        user_ortu, _ = self._buat_user('demo_ortu1', 'orang_tua', 'Bapak', 'Pratama')
        ortu, _ = OrangTua.objects.get_or_create(user=user_ortu)
        ortu.anak.add(siswa_map['demo_andi'], siswa_map['demo_eka'])

        # ---------- Tugas + nilai ----------
        nilai_4a = {
            'demo_andi': [95, 88],
            'demo_bunga': [78, 82],
            'demo_citra': [60, 55],
            'demo_dani': [88, 91],
        }
        nilai_4b = {
            'demo_eka': [90, 85],
            'demo_fajar': [65, 70],
            'demo_gita': [92, 89],
        }
        self._buat_tugas_dan_nilai(kelas_4a, guru, 'MTK', 'online', nilai_4a, 0, hari_ini, siswa_map)
        self._buat_tugas_dan_nilai(kelas_4a, guru, 'IPA', 'tulis', nilai_4a, 1, hari_ini, siswa_map)
        self._buat_tugas_dan_nilai(kelas_4b, guru, 'MTK', 'online', nilai_4b, 0, hari_ini, siswa_map)
        self._buat_tugas_dan_nilai(kelas_4b, guru, 'IND', 'tulis', nilai_4b, 1, hari_ini, siswa_map)

        # ---------- Absensi 10 hari terakhir ----------
        pola_absen = {
            'demo_andi': ['Hadir'] * 10,
            'demo_bunga': ['Hadir'] * 8 + ['Izin', 'Hadir'],
            'demo_citra': ['Hadir'] * 5 + ['Alpa'] * 3 + ['Hadir'] * 2,
            'demo_dani': ['Hadir'] * 9 + ['Sakit'],
            'demo_eka': ['Hadir'] * 10,
            'demo_fajar': ['Hadir'] * 6 + ['Alpa'] * 2 + ['Hadir'] * 2,
            'demo_gita': ['Hadir'] * 9 + ['Izin'],
        }
        for username, pola in pola_absen.items():
            siswa = siswa_map[username]
            for mundur, status in enumerate(reversed(pola), start=1):
                tanggal = hari_ini - datetime.timedelta(days=mundur)
                Absensi.objects.update_or_create(
                    siswa=siswa, tanggal=tanggal,
                    defaults={'status': status, 'dicatat_oleh': guru},
                )

        # ---------- Rekening bank dummy ----------
        RekeningBank.objects.get_or_create(
            nama_bank='Bank BCA', nomor_rekening='1234567890',
            defaults={'atas_nama': 'Yayasan Pendidikan SMILE', 'aktif': True},
        )

        # ---------- SPP bulan ini: 3 status berbeda ----------
        rencana_bayar = {
            'demo_andi': 'lunas',
            'demo_bunga': 'sebagian',   # persis skenario: bayar 200rb dari 300rb, sisa 100rb
            'demo_citra': 'belum',
            'demo_dani': 'lunas',
            'demo_eka': 'sebagian',
            'demo_fajar': 'belum',
            'demo_gita': 'lunas',
        }
        for username, rencana in rencana_bayar.items():
            siswa = siswa_map[username]
            tagihan, _ = TagihanSPP.objects.get_or_create(
                siswa=siswa, bulan=hari_ini.month, tahun=hari_ini.year,
                defaults={'nominal_tagihan': siswa.kelas.nominal_spp, 'dibuat_oleh': guru},
            )
            if tagihan.pembayaran.exists():
                continue  # sudah pernah di-seed, jangan dobel
            if rencana == 'lunas':
                PembayaranSPP.objects.create(
                    tagihan=tagihan, jumlah=tagihan.nominal_tagihan,
                    tanggal_bayar=hari_ini - datetime.timedelta(days=3),
                    catatan='Transfer lunas', dicatat_oleh=guru,
                )
            elif rencana == 'sebagian':
                PembayaranSPP.objects.create(
                    tagihan=tagihan, jumlah=200000,
                    tanggal_bayar=hari_ini - datetime.timedelta(days=3),
                    catatan='Cicilan pertama', dicatat_oleh=guru,
                )
            # 'belum' -> sengaja tidak dibuatkan PembayaranSPP sama sekali

        self.stdout.write(self.style.SUCCESS('Data demo berhasil dibuat / diperbarui.\n'))
        self._cetak_ringkasan()

    def _buat_user(self, username, role, first_name, last_name):
        user, dibuat = User.objects.get_or_create(
            username=username,
            defaults={'first_name': first_name, 'last_name': last_name},
        )
        if dibuat:
            user.set_password(DEMO_PASSWORD)
            user.save()
        Profile.objects.get_or_create(user=user, defaults={'role': role})
        return user, dibuat

    def _buat_tugas_dan_nilai(self, kelas, guru, mapel, jenis, peta_nilai, index_nilai, hari_ini, siswa_map):
        judul = f"Tugas {index_nilai + 1}"
        tugas, _ = Tugas.objects.get_or_create(
            judul=judul, kelas=kelas, mapel=mapel,
            defaults={
                'jenis': jenis, 'guru': guru,
                'tanggal': hari_ini - datetime.timedelta(days=14 - index_nilai),
                'deskripsi': 'Data contoh dari seed_demo.',
            },
        )
        for username, nilai_list in peta_nilai.items():
            NilaiTugas.objects.update_or_create(
                tugas=tugas, siswa=siswa_map[username],
                defaults={'nilai': nilai_list[index_nilai]},
            )

    def _cetak_ringkasan(self):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("AKUN DEMO (semua pakai password: demo12345)"))
        self.stdout.write("=" * 60)
        self.stdout.write("Guru wali kelas 4A & 4B : demo_guru1")
        self.stdout.write("Siswa 4A                : demo_andi, demo_bunga, demo_citra, demo_dani")
        self.stdout.write("Siswa 4B                : demo_eka, demo_fajar, demo_gita")
        self.stdout.write("Orang tua (anak: Andi 4A & Eka 4B) : demo_ortu1")
        self.stdout.write("-" * 60)
        self.stdout.write("Status SPP bulan ini:")
        self.stdout.write("  Lunas            : demo_andi, demo_dani, demo_gita")
        self.stdout.write("  Dibayar Sebagian : demo_bunga, demo_eka (bayar 200rb dari 300rb)")
        self.stdout.write("  Belum Bayar      : demo_citra, demo_fajar")
        self.stdout.write("=" * 60)
