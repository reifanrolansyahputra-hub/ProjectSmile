from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from akademik.models import Kelas, OrangTua, Siswa
from materi.models import Materi


def _buat_user(username, role, **extra):
    user = User.objects.create_user(username=username, password='pass12345', **extra)
    Profile.objects.create(user=user, role=role)
    return user


class LoginRedirectTest(TestCase):
    """Login & redirect per-role, termasuk role baru orang_tua."""

    def setUp(self):
        self.admin = _buat_user('r_admin', 'admin', is_staff=True, is_superuser=True)
        self.guru = _buat_user('r_guru', 'guru')
        self.murid = _buat_user('r_murid', 'murid')
        self.ortu = _buat_user('r_ortu', 'orang_tua')

    def test_redirect_per_role(self):
        harapan = {
            'r_admin': reverse('admin_dashboard'),
            'r_guru': reverse('guru_dashboard'),
            'r_murid': reverse('murid_dashboard'),
            'r_ortu': reverse('orangtua_dashboard'),
        }
        for username, url_tujuan in harapan.items():
            resp = self.client.post(reverse('login'), {'username': username, 'password': 'pass12345'})
            self.assertRedirects(resp, url_tujuan)
            self.client.logout()


class DashboardLamaTidakRusakTest(TestCase):
    """Pastikan dashboard admin/guru/murid yang sudah ada sebelumnya tetap render normal."""

    def setUp(self):
        self.admin = _buat_user('d_admin', 'admin', is_staff=True, is_superuser=True)
        self.guru = _buat_user('d_guru', 'guru', first_name='Bu Guru')
        self.murid_user = _buat_user('d_murid', 'murid', first_name='Murid')
        self.ortu_user = _buat_user('d_ortu', 'orang_tua')

        kelas = Kelas.objects.get(nama='1A')
        self.siswa = Siswa.objects.create(user=self.murid_user, kelas=kelas)
        self.ortu = OrangTua.objects.create(user=self.ortu_user)
        self.ortu.anak.add(self.siswa)

        Materi.objects.create(judul='Contoh Materi', mapel='MTK', kelas=1, guru=self.guru)

    def test_admin_dashboard_render(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('stats', resp.context)

    def test_guru_dashboard_render(self):
        self.client.force_login(self.guru)
        resp = self.client.get(reverse('guru_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_murid_dashboard_render(self):
        self.client.force_login(self.murid_user)
        resp = self.client.get(reverse('murid_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_orangtua_dashboard_render(self):
        self.client.force_login(self.ortu_user)
        resp = self.client.get(reverse('orangtua_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['siswa_aktif'].id, self.siswa.id)

    def test_kelola_materi_masih_jalan(self):
        self.client.force_login(self.guru)
        resp = self.client.get(reverse('kelola_materi'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Contoh Materi')

    def test_daftar_materi_murid_masih_jalan(self):
        self.client.force_login(self.murid_user)
        resp = self.client.get(reverse('daftar_materi'))
        self.assertEqual(resp.status_code, 200)

    def test_murid_tidak_bisa_lihat_dashboard_guru(self):
        self.client.force_login(self.murid_user)
        resp = self.client.get(reverse('guru_dashboard'))
        self.assertRedirects(resp, reverse('murid_dashboard'))

    def test_orangtua_bukan_murid_diarahkan_keluar_dashboard_murid(self):
        self.client.force_login(self.ortu_user)
        resp = self.client.get(reverse('murid_dashboard'))
        self.assertRedirects(resp, reverse('orangtua_dashboard'))
