from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from akademik.models import Kelas, OrangTua, Siswa

from .models import PembayaranSPP, RekeningBank, TagihanSPP


def _buat_user(username, role, **extra):
    user = User.objects.create_user(username=username, password='pass12345', **extra)
    Profile.objects.create(user=user, role=role)
    return user


class SetupSPPMixin:
    def setUp(self):
        self.kelas_4a = Kelas.objects.get(nama='4A')
        self.kelas_4a.nominal_spp = 300000
        self.kelas_4a.save()

        self.admin = _buat_user('p_admin', 'admin', is_staff=True, is_superuser=True)
        self.guru = _buat_user('p_guru', 'guru')

        self.user_budi = _buat_user('p_budi', 'murid', first_name='Budi')
        self.siswa_budi = Siswa.objects.create(user=self.user_budi, kelas=self.kelas_4a)

        self.user_ortu = _buat_user('p_ortu', 'orang_tua')
        self.ortu = OrangTua.objects.create(user=self.user_ortu)
        self.ortu.anak.add(self.siswa_budi)


class AksesAdminSPPTest(SetupSPPMixin, TestCase):

    def test_hanya_admin_boleh_kelola_spp(self):
        self.client.login(username='p_guru', password='pass12345')
        resp = self.client.get(reverse('kelola_spp'))
        self.assertNotEqual(resp.status_code, 200)

        self.client.login(username='p_admin', password='pass12345')
        resp = self.client.get(reverse('kelola_spp'))
        self.assertEqual(resp.status_code, 200)

    def test_murid_tidak_bisa_generate_tagihan_atau_catat_bayar(self):
        tagihan = TagihanSPP.objects.create(siswa=self.siswa_budi, bulan=10, tahun=2026, nominal_tagihan=300000)
        self.client.login(username='p_budi', password='pass12345')

        resp = self.client.post(reverse('generate_tagihan'), {'bulan': 10, 'tahun': 2026})
        self.assertEqual(TagihanSPP.objects.count(), 1)  # tidak nambah

        resp = self.client.post(reverse('catat_pembayaran', args=[tagihan.id]), {'jumlah': '100000'})
        self.assertEqual(PembayaranSPP.objects.count(), 0)


class GenerateTagihanTest(SetupSPPMixin, TestCase):

    def test_generate_tagihan_membuat_sesuai_nominal_kelas(self):
        self.client.login(username='p_admin', password='pass12345')
        self.client.post(reverse('generate_tagihan'), {'bulan': 11, 'tahun': 2026})

        tagihan = TagihanSPP.objects.get(siswa=self.siswa_budi, bulan=11, tahun=2026)
        self.assertEqual(tagihan.nominal_tagihan, 300000)
        self.assertEqual(tagihan.status, 'Belum Bayar')

    def test_generate_tagihan_tidak_duplikat_kalau_dipanggil_lagi(self):
        self.client.login(username='p_admin', password='pass12345')
        url = reverse('generate_tagihan')
        self.client.post(url, {'bulan': 11, 'tahun': 2026})
        self.client.post(url, {'bulan': 11, 'tahun': 2026})
        self.assertEqual(TagihanSPP.objects.filter(siswa=self.siswa_budi, bulan=11, tahun=2026).count(), 1)


class PembayaranStatusTest(SetupSPPMixin, TestCase):
    """Skenario persis dari permintaan: SPP 300rb, bayar 200rb -> sisa 100rb -> 'Dibayar Sebagian'."""

    def setUp(self):
        super().setUp()
        self.tagihan = TagihanSPP.objects.create(
            siswa=self.siswa_budi, bulan=10, tahun=2026, nominal_tagihan=300000,
        )

    def test_bayar_sebagian(self):
        self.client.login(username='p_admin', password='pass12345')
        self.client.post(reverse('catat_pembayaran', args=[self.tagihan.id]), {
            'jumlah': '200000', 'tanggal_bayar': '2026-10-05', 'catatan': 'Cicilan 1',
        })
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.total_dibayar, 200000)
        self.assertEqual(self.tagihan.sisa, 100000)
        self.assertEqual(self.tagihan.status, 'Dibayar Sebagian')

    def test_bayar_lunas_bertahap(self):
        self.client.login(username='p_admin', password='pass12345')
        url = reverse('catat_pembayaran', args=[self.tagihan.id])
        self.client.post(url, {'jumlah': '200000', 'tanggal_bayar': '2026-10-05'})
        self.client.post(url, {'jumlah': '100000', 'tanggal_bayar': '2026-10-20'})

        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.total_dibayar, 300000)
        self.assertEqual(self.tagihan.sisa, 0)
        self.assertEqual(self.tagihan.status, 'Lunas')

    def test_bayar_lebih_dari_tagihan_tetap_lunas_sisa_nol(self):
        self.client.login(username='p_admin', password='pass12345')
        self.client.post(reverse('catat_pembayaran', args=[self.tagihan.id]), {
            'jumlah': '350000', 'tanggal_bayar': '2026-10-05',
        })
        self.tagihan.refresh_from_db()
        self.assertEqual(self.tagihan.status, 'Lunas')
        self.assertEqual(self.tagihan.sisa, 0)  # tidak minus


class MuridOrtuLihatSPPTest(SetupSPPMixin, TestCase):

    def setUp(self):
        super().setUp()
        RekeningBank.objects.create(nama_bank='BCA', nomor_rekening='1234567890', atas_nama='Yayasan SMILE', aktif=True)
        TagihanSPP.objects.create(siswa=self.siswa_budi, bulan=10, tahun=2026, nominal_tagihan=300000)

    def test_murid_bisa_lihat_tagihan_sendiri_readonly(self):
        self.client.login(username='p_budi', password='pass12345')
        resp = self.client.get(reverse('pembayaran_murid'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['tagihan_list']), 1)

    def test_ortu_bisa_lihat_tagihan_anak_readonly(self):
        self.client.login(username='p_ortu', password='pass12345')
        resp = self.client.get(reverse('pembayaran_anak'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['tagihan_list']), 1)
