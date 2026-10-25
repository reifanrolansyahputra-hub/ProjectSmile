"""
Logika perhitungan ranking siswa.

Skor = (BOBOT_NILAI x rata-rata nilai tugas) + (BOBOT_KEHADIRAN x persen kehadiran)

- rata-rata nilai tugas: rata-rata semua NilaiTugas milik siswa (skala 0-100).
- persen kehadiran: (jumlah status "Hadir" / total absensi tercatat) x 100.
  Kalau belum ada absensi tercatat sama sekali, dianggap 100% (belum ada
  data yang memberatkan, bukan berarti siswa dianggap tidak hadir).

Catatan implementasi: rata-rata nilai dan hitung kehadiran sengaja dihitung
lewat DUA query annotate terpisah (bukan digabung dalam satu .annotate()),
karena meng-annotate dua relasi balik berbeda (nilai_tugas DAN absensi)
dalam satu query yang sama akan menyebabkan Django melakukan JOIN ganda
yang menggandakan baris ("fan-out"), sehingga Count/Avg jadi salah besar.
Dua query terpisah lalu digabung di Python itu justru lebih murah dan benar.
"""

from django.db.models import Avg, Count, Q

from .models import Siswa

BOBOT_NILAI = 0.7
BOBOT_KEHADIRAN = 0.3


def _hitung_dan_urutkan(queryset):
    siswa_ids = list(queryset.values_list('id', flat=True))
    if not siswa_ids:
        return []

    nilai_map = {
        row['id']: row
        for row in Siswa.objects.filter(id__in=siswa_ids).annotate(
            rata_nilai=Avg('nilai_tugas__nilai'),
            total_tugas=Count('nilai_tugas'),
        ).values('id', 'rata_nilai', 'total_tugas')
    }

    absen_map = {
        row['id']: row
        for row in Siswa.objects.filter(id__in=siswa_ids).annotate(
            total_hadir=Count('absensi', filter=Q(absensi__status='Hadir')),
            total_absen=Count('absensi'),
        ).values('id', 'total_hadir', 'total_absen')
    }

    hasil = []
    for siswa in queryset.select_related('user', 'kelas'):
        info_nilai = nilai_map.get(siswa.id, {})
        info_absen = absen_map.get(siswa.id, {})

        rata_nilai = float(info_nilai.get('rata_nilai') or 0)
        total_tugas = info_nilai.get('total_tugas') or 0

        total_absen = info_absen.get('total_absen') or 0
        total_hadir = info_absen.get('total_hadir') or 0
        persen_hadir = (total_hadir / total_absen * 100) if total_absen > 0 else 100.0

        skor = (rata_nilai * BOBOT_NILAI) + (persen_hadir * BOBOT_KEHADIRAN)

        hasil.append({
            'siswa': siswa,
            'rata_nilai': round(rata_nilai, 1),
            'total_tugas': total_tugas,
            'persen_hadir': round(persen_hadir, 1),
            'total_hadir': total_hadir,
            'total_absen': total_absen,
            'skor': round(skor, 2),
        })

    hasil.sort(key=lambda d: (-d['skor'], d['siswa'].nama_lengkap.lower()))
    for i, d in enumerate(hasil, start=1):
        d['rank'] = i
    return hasil


def ranking_kelas(kelas):
    """Ranking siswa aktif di satu Kelas (rombel) tertentu."""
    qs = Siswa.objects.filter(kelas=kelas, aktif=True)
    return _hitung_dan_urutkan(qs)


def ranking_paralel(tingkat):
    """Ranking siswa aktif di semua kelas pada satu tingkat (mis. semua kelas 4)."""
    qs = Siswa.objects.filter(kelas__tingkat=tingkat, aktif=True)
    return _hitung_dan_urutkan(qs)


def cari_baris(daftar_ranking, siswa_id):
    """Ambil baris ranking milik satu siswa tertentu dari hasil ranking_kelas/paralel."""
    for baris in daftar_ranking:
        if baris['siswa'].id == siswa_id:
            return baris
    return None
