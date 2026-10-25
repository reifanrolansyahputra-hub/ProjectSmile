from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from pembayaran.models import RekeningBank


class Command(BaseCommand):
    help = (
        "Menghapus semua akun & data yang dibuat oleh seed_demo (semua username "
        "berawalan 'demo_'), termasuk siswa/orangtua/tugas/nilai/absensi/tagihan "
        "miliknya (lewat cascade). Jalankan ini sebelum memakai aplikasi untuk "
        "sekolah sungguhan. Rekening bank dummy contoh (Bank BCA 1234567890) "
        "ikut dihapus juga."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        users = User.objects.filter(username__startswith='demo_')
        jumlah = users.count()
        daftar_username = list(users.values_list('username', flat=True))
        users.delete()  # cascade menghapus Siswa/OrangTua/Tugas/NilaiTugas/Absensi/TagihanSPP terkait

        rekening_dihapus, _ = RekeningBank.objects.filter(
            nama_bank='Bank BCA', nomor_rekening='1234567890',
        ).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Berhasil menghapus {jumlah} akun demo: {', '.join(daftar_username) or '(tidak ada)'}"
        ))
        self.stdout.write(self.style.SUCCESS("Rekening bank contoh juga sudah dihapus."))
