from .models import Profile


def get_role(user):
    """
    Mengembalikan role milik user: 'admin', 'guru', 'murid', 'orang_tua',
    atau None kalau user belum punya Profile sama sekali.
    """
    if not user or not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except Profile.DoesNotExist:
        return None


def get_siswa_aktif(user):
    """
    Dipakai di halaman MURID: mengembalikan objek Siswa milik user yang
    sedang login, atau None kalau akun murid ini belum ditautkan ke data
    Siswa oleh admin.
    """
    from akademik.models import Siswa
    try:
        return user.siswa
    except Siswa.DoesNotExist:
        return None
    except AttributeError:
        return None


def get_anak_aktif(request, orangtua):
    """
    Dipakai di halaman ORANG TUA: menentukan anak mana yang sedang dilihat.
    Diambil dari query string ?anak=<id_siswa>, divalidasi harus salah satu
    anak milik orangtua ini. Kalau tidak ada/tidak valid, pakai anak pertama.
    Mengembalikan tuple (siswa_aktif, daftar_semua_anak).
    """
    daftar_anak = orangtua.anak.select_related('kelas').order_by('user__first_name', 'user__username')

    if not daftar_anak.exists():
        return None, daftar_anak

    anak_id = request.GET.get('anak')
    if anak_id:
        dipilih = daftar_anak.filter(id=anak_id).first()
        if dipilih:
            return dipilih, daftar_anak

    return daftar_anak.first(), daftar_anak
