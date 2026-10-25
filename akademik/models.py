from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from materi.models import Materi


class Kelas(models.Model):
    """
    Satu rombongan belajar, misalnya "4A" atau "4B".
    `tingkat` dipakai untuk mengelompokkan kelas paralel (semua kelas 4,
    apapun namanya) untuk kebutuhan ranking paralel.
    """

    TINGKAT_CHOICES = Materi.KELAS_CHOICES

    nama = models.CharField(
        max_length=20,
        unique=True,
        help_text='Contoh: 4A, 4B, 5A, dst.'
    )

    tingkat = models.PositiveSmallIntegerField(
        choices=TINGKAT_CHOICES,
        help_text='Tingkat kelas untuk pengelompokan ranking paralel (mis. semua "Kelas 4").'
    )

    wali_kelas = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kelas_diwalikan',
        limit_choices_to={'profile__role': 'guru'},
        help_text='Opsional, hanya informasi. Semua guru tetap bisa mengelola kelas manapun.'
    )

    nominal_spp = models.PositiveIntegerField(
        default=300000,
        help_text='Nominal SPP per bulan untuk kelas ini (Rupiah).'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tingkat', 'nama']
        verbose_name = 'Kelas'
        verbose_name_plural = 'Kelas'

    def __str__(self):
        return self.nama

    @property
    def jumlah_siswa(self):
        return self.siswa_set.count()


class Siswa(models.Model):
    """
    Data tambahan untuk user dengan role 'murid': kelas dan NISN.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='siswa'
    )

    nisn = models.CharField(
        'NISN',
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    kelas = models.ForeignKey(
        Kelas,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='siswa_set'
    )

    JENIS_KELAMIN_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]
    jenis_kelamin = models.CharField(
        max_length=1,
        choices=JENIS_KELAMIN_CHOICES,
        blank=True
    )

    aktif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['kelas__tingkat', 'kelas__nama', 'user__first_name']
        verbose_name = 'Siswa'
        verbose_name_plural = 'Siswa'

    def __str__(self):
        nama = self.user.get_full_name() or self.user.username
        if self.kelas:
            return f"{nama} ({self.kelas.nama})"
        return nama

    @property
    def nama_lengkap(self):
        return self.user.get_full_name() or self.user.username


class OrangTua(models.Model):
    """
    Akun orang tua/wali. Satu orang tua bisa punya lebih dari satu anak
    (kakak-adik), dan satu siswa bisa ditautkan ke lebih dari satu akun
    orang tua (ayah & ibu masing-masing login sendiri).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='orangtua'
    )

    anak = models.ManyToManyField(
        Siswa,
        related_name='orang_tua',
        blank=True
    )

    no_hp = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Orang Tua'
        verbose_name_plural = 'Orang Tua'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Absensi(models.Model):
    """
    Satu baris = kehadiran satu siswa pada satu tanggal.
    """

    STATUS_CHOICES = [
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('Sakit', 'Sakit'),
        ('Alpa', 'Alpa'),
    ]

    siswa = models.ForeignKey(
        Siswa,
        on_delete=models.CASCADE,
        related_name='absensi'
    )

    tanggal = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Hadir')

    keterangan = models.CharField(max_length=255, blank=True)

    dicatat_oleh = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='absensi_dicatat'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('siswa', 'tanggal')]
        ordering = ['-tanggal']
        verbose_name = 'Absensi'
        verbose_name_plural = 'Absensi'

    def __str__(self):
        return f"{self.siswa} - {self.tanggal} - {self.status}"


class Tugas(models.Model):
    """
    Satu tugas/penilaian yang dibuat guru untuk satu kelas+mapel,
    misalnya "Tugas 1" mapel Matematika kelas 4A, jenis tulis di buku
    atau online.
    """

    MAPEL_CHOICES = Materi.MAPEL_CHOICES

    JENIS_CHOICES = [
        ('tulis', 'Tulis di Buku'),
        ('online', 'Online'),
    ]

    judul = models.CharField(max_length=150, help_text='Contoh: Tugas 1, Ulangan Harian 2, dst.')

    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE, related_name='tugas_set')

    mapel = models.CharField(max_length=10, choices=MAPEL_CHOICES)

    jenis = models.CharField(max_length=10, choices=JENIS_CHOICES, default='tulis')

    guru = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tugas_dibuat')

    deskripsi = models.TextField(blank=True)

    tanggal = models.DateField(help_text='Tanggal tugas diberikan/dikumpulkan.')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal', '-created_at']
        verbose_name = 'Tugas'
        verbose_name_plural = 'Tugas'

    def __str__(self):
        return f"{self.judul} - {self.kelas.nama} - {self.get_mapel_display()}"

    @property
    def jumlah_dinilai(self):
        return self.nilai_siswa.count()


class NilaiTugas(models.Model):
    """
    Nilai satu siswa untuk satu Tugas. Satu siswa hanya punya satu nilai
    per tugas (update_or_create dipakai di view input nilai).
    """

    tugas = models.ForeignKey(Tugas, on_delete=models.CASCADE, related_name='nilai_siswa')

    siswa = models.ForeignKey(Siswa, on_delete=models.CASCADE, related_name='nilai_tugas')

    nilai = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    catatan = models.CharField(max_length=255, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('tugas', 'siswa')]
        ordering = ['-updated_at']
        verbose_name = 'Nilai Tugas'
        verbose_name_plural = 'Nilai Tugas'

    def __str__(self):
        return f"{self.siswa} - {self.tugas.judul}: {self.nilai}"
