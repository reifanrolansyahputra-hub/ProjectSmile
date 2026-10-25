import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile

from .models import Absensi, Kelas, NilaiTugas, OrangTua, Siswa, Tugas
from .ranking import ranking_kelas, ranking_paralel


def _buat_user(username, role, **extra):
    user = User.objects.create_user(username=username, password='pass12345', **extra)
    Profile.objects.create(user=user, role=role)
    return user


class SetupRoleMixin:
    """Siapkan 1 kelas 4A dengan 2 siswa, 1 guru, 1 admin, 1 orang tua (anak: budi)."""

    def setUp(self):
        self.kelas_4a = Kelas.objects.get(nama='4A')
        self.kelas_4b = Kelas.objects.get(nama='4B')

        self.admin = _buat_user('t_admin', 'admin', is_staff=True, is_superuser=True)
        self.guru = _buat_user('t_guru', 'guru', first_name='Bu Guru')
        self.guru_lain = _buat_user('t_guru_lain', 'guru', first_name='Pak Guru Lain')

        self.user_budi = _buat_user('t_budi', 'murid', first_name='Budi')
        self.user_siti = _buat_user('t_siti', 'murid', first_name='Siti')
        self.siswa_budi = Siswa.objects.create(user=self.user_budi, kelas=self.kelas_4a)
        self.siswa_siti = Siswa.objects.create(user=self.user_siti, kelas=self.kelas_4a)

        self.user_ortu = _buat_user('t_ortu', 'orang_tua', first_name='Bapak Budi')
        self.ortu = OrangTua.objects.create(user=self.user_ortu)
        self.ortu.anak.add(self.siswa_budi)


class AksesPeranTest(SetupRoleMixin, TestCase):
    """Pastikan setiap role hanya bisa masuk ke halaman yang semestinya."""

    def test_guru_bisa_akses_absensi_dan_tugas(self):
        self.client.login(username='t_guru', password='pass12345')
        for url in [
            reverse('pilih_kelas_absensi'),
            reverse('absen_kelas', args=[self.kelas_4a.id]),
            reverse('daftar_tugas'),
            reverse('pilih_kelas_ranking'),
            reverse('lihat_ranking_guru', args=[self.kelas_4a.id]),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"{url} harusnya 200, dapat {resp.status_code}")

    def test_murid_tidak_bisa_akses_absen_kelas_guru(self):
        self.client.login(username='t_budi', password='pass12345')
        resp = self.client.get(reverse('absen_kelas', args=[self.kelas_4a.id]))
        self.assertNotEqual(resp.status_code, 200)  # harus diredirect, bukan diizinkan

    def test_murid_bisa_akses_halaman_sendiri(self):
        self.client.login(username='t_budi', password='pass12345')
        for url in [reverse('absensi_saya'), reverse('nilai_saya'), reverse('ranking_saya')]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_orangtua_tidak_bisa_akses_halaman_murid_atau_guru(self):
        self.client.login(username='t_ortu', password='pass12345')
        for url in [reverse('absensi_saya'), reverse('pilih_kelas_absensi')]:
            resp = self.client.get(url)
            self.assertNotEqual(resp.status_code, 200)

    def test_orangtua_bisa_akses_data_anak(self):
        self.client.login(username='t_ortu', password='pass12345')
        for url in [reverse('absensi_anak'), reverse('nilai_anak'), reverse('ranking_anak')]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.context['siswa'].id, self.siswa_budi.id)

    def test_tamu_belum_login_diarahkan_ke_login(self):
        resp = self.client.get(reverse('absensi_saya'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.url)


class AbsensiTest(SetupRoleMixin, TestCase):

    def test_guru_input_absensi_tersimpan(self):
        self.client.login(username='t_guru', password='pass12345')
        tanggal = datetime.date(2026, 10, 20)
        resp = self.client.post(reverse('absen_kelas', args=[self.kelas_4a.id]), {
            'tanggal': tanggal.isoformat(),
            f'status_{self.siswa_budi.id}': 'Hadir',
            f'status_{self.siswa_siti.id}': 'Izin',
            f'keterangan_{self.siswa_siti.id}': 'Sakit demam',
        })
        self.assertEqual(resp.status_code, 302)

        a_budi = Absensi.objects.get(siswa=self.siswa_budi, tanggal=tanggal)
        a_siti = Absensi.objects.get(siswa=self.siswa_siti, tanggal=tanggal)
        self.assertEqual(a_budi.status, 'Hadir')
        self.assertEqual(a_siti.status, 'Izin')

    def test_absensi_diedit_tidak_duplikat(self):
        """Mengirim absensi 2x di tanggal sama harus UPDATE, bukan membuat baris baru."""
        self.client.login(username='t_guru', password='pass12345')
        tanggal = datetime.date(2026, 10, 21)
        url = reverse('absen_kelas', args=[self.kelas_4a.id])

        self.client.post(url, {'tanggal': tanggal.isoformat(), f'status_{self.siswa_budi.id}': 'Hadir'})
        self.client.post(url, {'tanggal': tanggal.isoformat(), f'status_{self.siswa_budi.id}': 'Alpa'})

        self.assertEqual(Absensi.objects.filter(siswa=self.siswa_budi, tanggal=tanggal).count(), 1)
        self.assertEqual(Absensi.objects.get(siswa=self.siswa_budi, tanggal=tanggal).status, 'Alpa')


class TugasNilaiTest(SetupRoleMixin, TestCase):

    def test_guru_tambah_tugas_dan_input_nilai(self):
        self.client.login(username='t_guru', password='pass12345')
        self.client.post(reverse('tambah_tugas'), {
            'judul': 'Tugas 1',
            'kelas': self.kelas_4a.id,
            'mapel': 'MTK',
            'jenis': 'online',
            'tanggal': '2026-10-15',
            'deskripsi': 'Latihan penjumlahan',
        })
        tugas = Tugas.objects.get(judul='Tugas 1')
        self.assertEqual(tugas.jenis, 'online')
        self.assertEqual(tugas.guru, self.guru)

        resp = self.client.post(reverse('input_nilai', args=[tugas.id]), {
            f'nilai_{self.siswa_budi.id}': '90',
            f'nilai_{self.siswa_siti.id}': '75',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(NilaiTugas.objects.get(tugas=tugas, siswa=self.siswa_budi).nilai, 90)
        self.assertEqual(NilaiTugas.objects.get(tugas=tugas, siswa=self.siswa_siti).nilai, 75)

    def test_guru_lain_tidak_bisa_nilai_tugas_orang(self):
        tugas = Tugas.objects.create(
            judul='Tugas Rahasia', kelas=self.kelas_4a, mapel='IPA',
            jenis='tulis', guru=self.guru, tanggal=datetime.date(2026, 10, 10),
        )
        self.client.login(username='t_guru_lain', password='pass12345')
        resp = self.client.get(reverse('input_nilai', args=[tugas.id]))
        self.assertEqual(resp.status_code, 404)

    def test_nilai_di_luar_rentang_dipotong_ke_0_100(self):
        self.client.login(username='t_guru', password='pass12345')
        tugas = Tugas.objects.create(
            judul='Tugas Batas', kelas=self.kelas_4a, mapel='MTK',
            jenis='tulis', guru=self.guru, tanggal=datetime.date(2026, 10, 10),
        )
        self.client.post(reverse('input_nilai', args=[tugas.id]), {
            f'nilai_{self.siswa_budi.id}': '150',
            f'nilai_{self.siswa_siti.id}': '-20',
        })
        self.assertEqual(NilaiTugas.objects.get(tugas=tugas, siswa=self.siswa_budi).nilai, 100)
        self.assertEqual(NilaiTugas.objects.get(tugas=tugas, siswa=self.siswa_siti).nilai, 0)


class RankingTest(SetupRoleMixin, TestCase):

    def _beri_nilai(self, siswa, tugas, nilai):
        NilaiTugas.objects.create(tugas=tugas, siswa=siswa, nilai=nilai)

    def test_perhitungan_skor_dan_urutan_benar(self):
        tugas = Tugas.objects.create(
            judul='T1', kelas=self.kelas_4a, mapel='MTK', jenis='tulis',
            guru=self.guru, tanggal=datetime.date(2026, 10, 1),
        )
        # Budi: nilai 100, hadir 10/10 (100%) -> skor = 100*0.7 + 100*0.3 = 100
        # Siti: nilai 50, hadir 5/10 (50%)    -> skor = 50*0.7 + 50*0.3 = 50
        self._beri_nilai(self.siswa_budi, tugas, 100)
        self._beri_nilai(self.siswa_siti, tugas, 50)

        base = datetime.date(2026, 9, 1)
        for i in range(10):
            Absensi.objects.create(siswa=self.siswa_budi, tanggal=base + datetime.timedelta(days=i), status='Hadir')
        for i in range(10):
            status = 'Hadir' if i < 5 else 'Alpa'
            Absensi.objects.create(siswa=self.siswa_siti, tanggal=base + datetime.timedelta(days=i), status=status)

        hasil = ranking_kelas(self.kelas_4a)
        self.assertEqual(hasil[0]['siswa'].id, self.siswa_budi.id)
        self.assertEqual(hasil[0]['rank'], 1)
        self.assertAlmostEqual(hasil[0]['skor'], 100.0)
        self.assertEqual(hasil[1]['siswa'].id, self.siswa_siti.id)
        self.assertAlmostEqual(hasil[1]['skor'], 50.0)

    def test_ranking_tidak_fan_out_dengan_banyak_tugas_dan_absensi(self):
        """Siswa dengan banyak baris nilai & absensi tidak boleh membuat rata-rata/hitung meledak (bug JOIN ganda)."""
        for i in range(5):
            t = Tugas.objects.create(
                judul=f'T{i}', kelas=self.kelas_4a, mapel='MTK', jenis='tulis',
                guru=self.guru, tanggal=datetime.date(2026, 10, 1) + datetime.timedelta(days=i),
            )
            self._beri_nilai(self.siswa_budi, t, 80)

        base = datetime.date(2026, 9, 1)
        for i in range(20):
            Absensi.objects.create(siswa=self.siswa_budi, tanggal=base + datetime.timedelta(days=i), status='Hadir')

        hasil = ranking_kelas(self.kelas_4a)
        baris_budi = next(h for h in hasil if h['siswa'].id == self.siswa_budi.id)
        self.assertEqual(baris_budi['total_tugas'], 5)
        self.assertEqual(baris_budi['total_absen'], 20)
        self.assertEqual(baris_budi['rata_nilai'], 80.0)
        self.assertEqual(baris_budi['persen_hadir'], 100.0)

    def test_ranking_paralel_mencakup_semua_kelas_setingkat(self):
        user_c = _buat_user('t_charlie', 'murid', first_name='Charlie')
        siswa_c = Siswa.objects.create(user=user_c, kelas=self.kelas_4b)  # beda kelas, tingkat sama (4)

        hasil_paralel = ranking_paralel(4)
        id_siswa_di_hasil = {h['siswa'].id for h in hasil_paralel}
        self.assertIn(self.siswa_budi.id, id_siswa_di_hasil)
        self.assertIn(self.siswa_siti.id, id_siswa_di_hasil)
        self.assertIn(siswa_c.id, id_siswa_di_hasil)

    def test_siswa_tanpa_data_dapat_kehadiran_100_persen_default(self):
        """Siswa baru tanpa absensi sama sekali tidak dirugikan (dianggap 100% dulu, bukan 0%)."""
        hasil = ranking_kelas(self.kelas_4a)
        baris_siti = next(h for h in hasil if h['siswa'].id == self.siswa_siti.id)
        self.assertEqual(baris_siti['persen_hadir'], 100.0)
        self.assertEqual(baris_siti['total_absen'], 0)
