import datetime
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import get_anak_aktif, get_role, get_siswa_aktif

from .models import Absensi, Kelas, NilaiTugas, Siswa, Tugas
from .ranking import cari_baris, ranking_kelas, ranking_paralel


def _parse_tanggal(nilai, default=None):
    if not nilai:
        return default or timezone.localdate()
    try:
        return date.fromisoformat(nilai)
    except ValueError:
        return default or timezone.localdate()


def _kelompok_kelas():
    """Semua kelas, dikelompokkan per tingkat: [(1, [1A, 1B]), (2, [2A, 2B]), ...]"""
    kelas_semua = Kelas.objects.all().order_by('tingkat', 'nama')
    kelompok = {}
    for k in kelas_semua:
        kelompok.setdefault(k.tingkat, []).append(k)
    return sorted(kelompok.items())


def _ringkasan_absensi(siswa):
    total = siswa.absensi.count()
    hadir = siswa.absensi.filter(status='Hadir').count()
    izin = siswa.absensi.filter(status='Izin').count()
    sakit = siswa.absensi.filter(status='Sakit').count()
    alpa = siswa.absensi.filter(status='Alpa').count()
    persen = round(hadir / total * 100, 1) if total else 0
    return {'total': total, 'hadir': hadir, 'izin': izin, 'sakit': sakit, 'alpa': alpa, 'persen': persen}


# ===========================================================
# GURU (admin juga diizinkan, mengikuti pola app materi)
# ===========================================================

@login_required
def pilih_kelas_absensi(request):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')
    return render(request, 'akademik/pilih_kelas.html', {
        'kelompok_kelas': _kelompok_kelas(),
        'judul_halaman': 'Pilih Kelas untuk Absensi',
        'subjudul': 'Klik kelas yang mau diabsen hari ini.',
        'url_name': 'absen_kelas',
        'ikon': '🗓️',
    })


@login_required
def absen_kelas(request, kelas_id):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    kelas = get_object_or_404(Kelas, id=kelas_id)
    siswa_list = Siswa.objects.filter(kelas=kelas, aktif=True).select_related('user').order_by('user__first_name', 'user__username')

    if request.method == 'POST':
        tanggal = _parse_tanggal(request.POST.get('tanggal'))
        for s in siswa_list:
            status = request.POST.get(f'status_{s.id}')
            keterangan = request.POST.get(f'keterangan_{s.id}', '').strip()
            if status in dict(Absensi.STATUS_CHOICES):
                Absensi.objects.update_or_create(
                    siswa=s, tanggal=tanggal,
                    defaults={'status': status, 'keterangan': keterangan, 'dicatat_oleh': request.user},
                )
        messages.success(request, f"Absensi {kelas.nama} tanggal {tanggal.strftime('%d-%m-%Y')} berhasil disimpan.")
        return redirect(f"/guru/absensi/{kelas.id}/?tanggal={tanggal.isoformat()}")

    tanggal = _parse_tanggal(request.GET.get('tanggal'))
    absensi_tanggal_ini = {a.siswa_id: a for a in Absensi.objects.filter(siswa__in=siswa_list, tanggal=tanggal)}

    data_siswa = []
    for s in siswa_list:
        a = absensi_tanggal_ini.get(s.id)
        data_siswa.append({
            'siswa': s,
            'status': a.status if a else 'Hadir',
            'keterangan': a.keterangan if a else '',
        })

    rekap = [{'siswa': s, **_ringkasan_absensi(s)} for s in siswa_list]

    satu_hari = datetime.timedelta(days=1)

    return render(request, 'akademik/absensi_form.html', {
        'kelas': kelas,
        'tanggal': tanggal,
        'tanggal_sebelum': tanggal - satu_hari,
        'tanggal_sesudah': tanggal + satu_hari,
        'data_siswa': data_siswa,
        'rekap': rekap,
        'status_choices': Absensi.STATUS_CHOICES,
    })


@login_required
def daftar_tugas(request):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    if get_role(request.user) == 'admin':
        tugas_list = Tugas.objects.all().select_related('kelas', 'guru')
    else:
        tugas_list = Tugas.objects.filter(guru=request.user).select_related('kelas', 'guru')

    kelas_id = request.GET.get('kelas')
    mapel = request.GET.get('mapel')
    if kelas_id:
        tugas_list = tugas_list.filter(kelas_id=kelas_id)
    if mapel:
        tugas_list = tugas_list.filter(mapel=mapel)

    return render(request, 'akademik/tugas_list.html', {
        'tugas_list': tugas_list,
        'kelas_semua': Kelas.objects.all(),
        'mapel_choices': Tugas.MAPEL_CHOICES,
        'jenis_choices': Tugas.JENIS_CHOICES,
        'kelas_aktif': kelas_id,
        'mapel_aktif': mapel,
    })


@login_required
def tambah_tugas(request):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    if request.method == 'POST':
        judul = request.POST.get('judul', '').strip()
        kelas_id = request.POST.get('kelas')
        mapel = request.POST.get('mapel')
        jenis = request.POST.get('jenis')
        deskripsi = request.POST.get('deskripsi', '').strip()
        tanggal = _parse_tanggal(request.POST.get('tanggal'))

        if judul and kelas_id and mapel and jenis:
            Tugas.objects.create(
                judul=judul, kelas_id=kelas_id, mapel=mapel, jenis=jenis,
                tanggal=tanggal, deskripsi=deskripsi, guru=request.user,
            )
            messages.success(request, f"Tugas '{judul}' berhasil ditambahkan.")
        else:
            messages.error(request, "Judul, kelas, mapel, dan jenis wajib diisi.")

    return redirect('daftar_tugas')


def _tugas_queryset_untuk(user):
    if get_role(user) == 'admin':
        return Tugas.objects.all()
    return Tugas.objects.filter(guru=user)


@login_required
def edit_tugas(request, id):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    tugas = get_object_or_404(_tugas_queryset_untuk(request.user), id=id)

    if request.method == 'POST':
        tugas.judul = request.POST.get('judul', tugas.judul).strip()
        tugas.kelas_id = request.POST.get('kelas') or tugas.kelas_id
        tugas.mapel = request.POST.get('mapel') or tugas.mapel
        tugas.jenis = request.POST.get('jenis') or tugas.jenis
        tugas.tanggal = _parse_tanggal(request.POST.get('tanggal'), default=tugas.tanggal)
        tugas.deskripsi = request.POST.get('deskripsi', '').strip()
        tugas.save()
        messages.success(request, f"Tugas '{tugas.judul}' berhasil diperbarui.")
        return redirect('daftar_tugas')

    tugas_list = _tugas_queryset_untuk(request.user).select_related('kelas', 'guru')
    return render(request, 'akademik/tugas_list.html', {
        'tugas_list': tugas_list,
        'kelas_semua': Kelas.objects.all(),
        'mapel_choices': Tugas.MAPEL_CHOICES,
        'jenis_choices': Tugas.JENIS_CHOICES,
        'edit_data': tugas,
    })


@login_required
def hapus_tugas(request, id):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    tugas = get_object_or_404(_tugas_queryset_untuk(request.user), id=id)
    judul = tugas.judul
    tugas.delete()
    messages.success(request, f"Tugas '{judul}' berhasil dihapus.")
    return redirect('daftar_tugas')


@login_required
def input_nilai(request, tugas_id):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    tugas = get_object_or_404(_tugas_queryset_untuk(request.user), id=tugas_id)
    siswa_list = Siswa.objects.filter(kelas=tugas.kelas, aktif=True).select_related('user').order_by('user__first_name', 'user__username')

    if request.method == 'POST':
        for s in siswa_list:
            nilai_mentah = request.POST.get(f'nilai_{s.id}', '').strip()
            catatan = request.POST.get(f'catatan_{s.id}', '').strip()
            if nilai_mentah == '':
                continue
            try:
                nilai = int(float(nilai_mentah))
            except ValueError:
                continue
            nilai = max(0, min(100, nilai))
            NilaiTugas.objects.update_or_create(
                tugas=tugas, siswa=s,
                defaults={'nilai': nilai, 'catatan': catatan},
            )
        messages.success(request, f"Nilai untuk '{tugas.judul}' berhasil disimpan.")
        return redirect('input_nilai', tugas_id=tugas.id)

    nilai_ada = {n.siswa_id: n for n in NilaiTugas.objects.filter(tugas=tugas)}
    data_siswa = [
        {
            'siswa': s,
            'nilai': nilai_ada[s.id].nilai if s.id in nilai_ada else '',
            'catatan': nilai_ada[s.id].catatan if s.id in nilai_ada else '',
        }
        for s in siswa_list
    ]

    return render(request, 'akademik/nilai_form.html', {
        'tugas': tugas,
        'data_siswa': data_siswa,
    })


@login_required
def pilih_kelas_ranking(request):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')
    return render(request, 'akademik/pilih_kelas.html', {
        'kelompok_kelas': _kelompok_kelas(),
        'judul_halaman': 'Pilih Kelas untuk Lihat Ranking',
        'subjudul': 'Klik salah satu kelas untuk melihat papan ranking-nya.',
        'url_name': 'lihat_ranking_guru',
        'ikon': '🏆',
    })


@login_required
def lihat_ranking_guru(request, kelas_id):
    if get_role(request.user) not in ('admin', 'guru'):
        return redirect('murid_dashboard')

    kelas = get_object_or_404(Kelas, id=kelas_id)
    mode = 'paralel' if request.GET.get('mode') == 'paralel' else 'kelas'
    hasil = ranking_paralel(kelas.tingkat) if mode == 'paralel' else ranking_kelas(kelas)

    return render(request, 'akademik/ranking.html', {
        'kelas': kelas,
        'mode': mode,
        'hasil': hasil,
        'base_template': 'portal/guru_dashboard.html',
        'tampilan': 'guru',
    })


# ===========================================================
# MURID
# ===========================================================

@login_required
def absensi_saya(request):
    if get_role(request.user) != 'murid':
        return redirect('guru_dashboard')

    siswa = get_siswa_aktif(request.user)
    ringkasan = _ringkasan_absensi(siswa) if siswa else None

    return render(request, 'akademik/absensi_riwayat.html', {
        'siswa': siswa,
        'riwayat': siswa.absensi.all()[:60] if siswa else [],
        'ringkasan': ringkasan,
        'base_template': 'portal/dashboardmurid.html',
        'tampilan': 'murid',
    })


@login_required
def nilai_saya(request):
    if get_role(request.user) != 'murid':
        return redirect('guru_dashboard')

    siswa = get_siswa_aktif(request.user)
    nilai_list = siswa.nilai_tugas.select_related('tugas', 'tugas__kelas').all() if siswa else []
    rata2 = round(sum(n.nilai for n in nilai_list) / len(nilai_list), 1) if nilai_list else None

    return render(request, 'akademik/nilai_list.html', {
        'siswa': siswa,
        'nilai_list': nilai_list,
        'rata2': rata2,
        'base_template': 'portal/dashboardmurid.html',
        'tampilan': 'murid',
    })


@login_required
def ranking_saya(request):
    if get_role(request.user) != 'murid':
        return redirect('guru_dashboard')

    siswa = get_siswa_aktif(request.user)
    context = {'siswa': siswa, 'base_template': 'portal/dashboardmurid.html', 'tampilan': 'murid'}

    if not siswa or not siswa.kelas:
        return render(request, 'akademik/ranking.html', context)

    mode = 'paralel' if request.GET.get('mode') == 'paralel' else 'kelas'
    kelas = siswa.kelas
    hasil = ranking_paralel(kelas.tingkat) if mode == 'paralel' else ranking_kelas(kelas)

    context.update({
        'kelas': kelas,
        'mode': mode,
        'hasil': hasil,
        'baris_saya': cari_baris(hasil, siswa.id),
    })
    return render(request, 'akademik/ranking.html', context)


# ===========================================================
# ORANG TUA
# ===========================================================

@login_required
def absensi_anak(request):
    if get_role(request.user) != 'orang_tua':
        return redirect('murid_dashboard')

    orangtua = getattr(request.user, 'orangtua', None)
    context = {'base_template': 'portal/dashboardortu.html', 'tampilan': 'ortu'}
    if not orangtua:
        return render(request, 'akademik/absensi_riwayat.html', context)

    siswa, daftar_anak = get_anak_aktif(request, orangtua)
    context['daftar_anak'] = daftar_anak
    context['siswa'] = siswa
    if siswa:
        context['riwayat'] = siswa.absensi.all()[:60]
        context['ringkasan'] = _ringkasan_absensi(siswa)
    return render(request, 'akademik/absensi_riwayat.html', context)


@login_required
def nilai_anak(request):
    if get_role(request.user) != 'orang_tua':
        return redirect('murid_dashboard')

    orangtua = getattr(request.user, 'orangtua', None)
    context = {'base_template': 'portal/dashboardortu.html', 'tampilan': 'ortu'}
    if not orangtua:
        return render(request, 'akademik/nilai_list.html', context)

    siswa, daftar_anak = get_anak_aktif(request, orangtua)
    context['daftar_anak'] = daftar_anak
    context['siswa'] = siswa
    if siswa:
        nilai_list = siswa.nilai_tugas.select_related('tugas', 'tugas__kelas').all()
        context['nilai_list'] = nilai_list
        context['rata2'] = round(sum(n.nilai for n in nilai_list) / len(nilai_list), 1) if nilai_list else None
    return render(request, 'akademik/nilai_list.html', context)


@login_required
def ranking_anak(request):
    if get_role(request.user) != 'orang_tua':
        return redirect('murid_dashboard')

    orangtua = getattr(request.user, 'orangtua', None)
    context = {'base_template': 'portal/dashboardortu.html', 'tampilan': 'ortu'}
    if not orangtua:
        return render(request, 'akademik/ranking.html', context)

    siswa, daftar_anak = get_anak_aktif(request, orangtua)
    context['daftar_anak'] = daftar_anak
    context['siswa'] = siswa

    if siswa and siswa.kelas:
        mode = 'paralel' if request.GET.get('mode') == 'paralel' else 'kelas'
        kelas = siswa.kelas
        hasil = ranking_paralel(kelas.tingkat) if mode == 'paralel' else ranking_kelas(kelas)
        context.update({
            'kelas': kelas,
            'mode': mode,
            'hasil': hasil,
            'baris_saya': cari_baris(hasil, siswa.id),
        })

    return render(request, 'akademik/ranking.html', context)
