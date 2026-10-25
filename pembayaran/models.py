from django.contrib.auth.models import User
from django.db import models

from akademik.models import Siswa


class RekeningBank(models.Model):
    """
    Rekening bank (dummy) yang ditampilkan ke orang tua/murid sebagai
    tujuan transfer SPP. Pencatatan pembayaran tetap dilakukan manual
    oleh admin, belum ada integrasi payment gateway.
    """

    nama_bank = models.CharField(max_length=100, help_text='Contoh: BCA, BRI, Mandiri')

    nomor_rekening = models.CharField(max_length=50)

    atas_nama = models.CharField(max_length=150)

    aktif = models.BooleanField(
        default=True,
        help_text='Hanya rekening aktif yang ditampilkan ke murid/orang tua.'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-aktif', 'nama_bank']
        verbose_name = 'Rekening Bank'
        verbose_name_plural = 'Rekening Bank'

    def __str__(self):
        return f"{self.nama_bank} - {self.nomor_rekening} a.n. {self.atas_nama}"


class TagihanSPP(models.Model):
    """
    Tagihan SPP satu siswa untuk satu bulan+tahun tertentu.
    `nominal_tagihan` disalin dari Kelas.nominal_spp saat tagihan dibuat,
    supaya perubahan nominal SPP di kemudian hari tidak mengubah tagihan
    bulan-bulan yang sudah lewat.
    """

    BULAN_CHOICES = [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember'),
    ]

    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='tagihan_spp')

    bulan = models.PositiveSmallIntegerField(choices=BULAN_CHOICES)

    tahun = models.PositiveIntegerField()

    nominal_tagihan = models.PositiveIntegerField(help_text='Nominal SPP bulan ini (Rupiah).')

    dibuat_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tagihan_dibuat'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('siswa', 'bulan', 'tahun')]
        ordering = ['-tahun', '-bulan', 'siswa__user__first_name']
        verbose_name = 'Tagihan SPP'
        verbose_name_plural = 'Tagihan SPP'

    def __str__(self):
        return f"SPP {self.get_bulan_display()} {self.tahun} - {self.siswa}"

    @property
    def total_dibayar(self):
        total = self.pembayaran.aggregate(total=models.Sum('jumlah'))['total']
        return total or 0

    @property
    def sisa(self):
        sisa = self.nominal_tagihan - self.total_dibayar
        return sisa if sisa > 0 else 0

    @property
    def status(self):
        dibayar = self.total_dibayar
        if dibayar <= 0:
            return 'Belum Bayar'
        elif dibayar < self.nominal_tagihan:
            return 'Dibayar Sebagian'
        return 'Lunas'

    @property
    def lunas(self):
        return self.status == 'Lunas'


class PembayaranSPP(models.Model):
    """
    Satu kali setoran/pembayaran yang dicatat admin terhadap sebuah
    TagihanSPP. Satu tagihan bisa punya beberapa baris pembayaran
    (dicicil), total semuanya dibandingkan dengan nominal_tagihan untuk
    menentukan status lunas/belum.
    """

    tagihan = models.ForeignKey(TagihanSPP, on_delete=models.CASCADE, related_name='pembayaran')

    tanggal_bayar = models.DateField()

    jumlah = models.PositiveIntegerField()

    dicatat_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pembayaran_dicatat'
    )

    catatan = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_bayar', '-created_at']
        verbose_name = 'Pembayaran SPP'
        verbose_name_plural = 'Pembayaran SPP'

    def __str__(self):
        return f"Rp{self.jumlah:,} - {self.tagihan}".replace(',', '.')
