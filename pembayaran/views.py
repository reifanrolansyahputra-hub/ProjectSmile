from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import get_anak_aktif, get_role, get_siswa_aktif
from akademik.models import Kelas, Siswa

from .models import PembayaranSPP, RekeningBank, TagihanSPP


def _parse_tanggal(nilai):
    if not nilai:
        return timezone.localdate()
    try:
        return date.fromisoformat(nilai)
    except ValueError:
        return timezone.localdate()


def _redirect_sesuai_role(user):
    role = get_role(user)
    if role == 'guru':
        return redirect('guru_dashboard')
    if role == 'murid':
        return redirect('murid_dashboard')
    if role == 'orang_tua':
        return redirect('orangtua_dashboard')
    return redirect('home')


def _format_rupiah(nilai):
    return f"Rp{nilai:,}".replace(',', '.')


# ===========================================================
# ADMIN
# ===========================================================

@login_required
def kelola_spp(request):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    kelas_id = request.GET.get('kelas')
    bulan = request.GET.get('bulan')
    tahun = request.GET.get('tahun')
    status_filter = request.GET.get('status')

    tagihan_qs = TagihanSPP.objects.select_related('siswa', 'siswa__kelas', 'siswa__user')
    if kelas_id:
        tagihan_qs = tagihan_qs.filter(siswa__kelas_id=kelas_id)
    if bulan:
        tagihan_qs = tagihan_qs.filter(bulan=bulan)
    if tahun:
        tagihan_qs = tagihan_qs.filter(tahun=tahun)

    tagihan_list = list(tagihan_qs)
    if status_filter:
        tagihan_list = [t for t in tagihan_list if t.status == status_filter]

    sekarang = timezone.localdate()

    return render(request, 'pembayaran/kelola_spp.html', {
        'rekening_list': RekeningBank.objects.all(),
        'tagihan_list': tagihan_list,
        'kelas_semua': Kelas.objects.all(),
        'bulan_choices': TagihanSPP.BULAN_CHOICES,
        'tahun_pilihan': [sekarang.year - 1, sekarang.year, sekarang.year + 1],
        'bulan_sekarang': sekarang.month,
        'tahun_sekarang': sekarang.year,
        'kelas_aktif': kelas_id,
        'bulan_aktif': bulan,
        'tahun_aktif': tahun,
        'status_aktif': status_filter,
    })


@login_required
def generate_tagihan(request):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    if request.method == 'POST':
        try:
            bulan = int(request.POST.get('bulan'))
            tahun = int(request.POST.get('tahun'))
        except (TypeError, ValueError):
            messages.error(request, "Bulan/tahun tidak valid.")
            return redirect('kelola_spp')

        dibuat = 0
        siswa_list = Siswa.objects.filter(aktif=True, kelas__isnull=False).select_related('kelas')
        for s in siswa_list:
            _, created = TagihanSPP.objects.get_or_create(
                siswa=s, bulan=bulan, tahun=tahun,
                defaults={'nominal_tagihan': s.kelas.nominal_spp, 'dibuat_oleh': request.user},
            )
            if created:
                dibuat += 1

        nama_bulan = dict(TagihanSPP.BULAN_CHOICES).get(bulan, bulan)
        if dibuat:
            messages.success(request, f"{dibuat} tagihan SPP baru dibuat untuk {nama_bulan} {tahun}.")
        else:
            messages.success(request, f"Tidak ada tagihan baru — semua siswa aktif sudah punya tagihan {nama_bulan} {tahun}.")

    return redirect('kelola_spp')


@login_required
def catat_pembayaran(request, tagihan_id):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    tagihan = get_object_or_404(
        TagihanSPP.objects.select_related('siswa', 'siswa__kelas', 'siswa__user'),
        id=tagihan_id,
    )

    if request.method == 'POST':
        jumlah_mentah = request.POST.get('jumlah', '').strip()
        catatan = request.POST.get('catatan', '').strip()
        try:
            jumlah = int(float(jumlah_mentah))
        except (TypeError, ValueError):
            jumlah = 0

        if jumlah > 0:
            PembayaranSPP.objects.create(
                tagihan=tagihan,
                jumlah=jumlah,
                tanggal_bayar=_parse_tanggal(request.POST.get('tanggal_bayar')),
                catatan=catatan,
                dicatat_oleh=request.user,
            )
            messages.success(
                request,
                f"Pembayaran {_format_rupiah(jumlah)} untuk {tagihan.siswa.nama_lengkap} dicatat. "
                f"Status tagihan sekarang: {tagihan.status}."
            )
        else:
            messages.error(request, "Jumlah pembayaran harus lebih dari 0.")
        return redirect('kelola_spp')

    return render(request, 'pembayaran/catat_pembayaran.html', {
        'tagihan': tagihan,
    })


@login_required
def tambah_rekening(request):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    if request.method == 'POST':
        nama_bank = request.POST.get('nama_bank', '').strip()
        nomor_rekening = request.POST.get('nomor_rekening', '').strip()
        atas_nama = request.POST.get('atas_nama', '').strip()
        if nama_bank and nomor_rekening and atas_nama:
            RekeningBank.objects.create(
                nama_bank=nama_bank, nomor_rekening=nomor_rekening, atas_nama=atas_nama,
            )
            messages.success(request, "Rekening bank berhasil ditambahkan.")
        else:
            messages.error(request, "Nama bank, nomor rekening, dan atas nama wajib diisi.")

    return redirect('kelola_spp')


@login_required
def toggle_rekening(request, id):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    rekening = get_object_or_404(RekeningBank, id=id)
    rekening.aktif = not rekening.aktif
    rekening.save()
    return redirect('kelola_spp')


@login_required
def hapus_rekening(request, id):
    if get_role(request.user) != 'admin':
        return _redirect_sesuai_role(request.user)

    rekening = get_object_or_404(RekeningBank, id=id)
    rekening.delete()
    messages.success(request, "Rekening bank berhasil dihapus.")
    return redirect('kelola_spp')


# ===========================================================
# MURID & ORANG TUA (lihat saja, tidak bisa ubah apapun)
# ===========================================================

@login_required
def pembayaran_murid(request):
    if get_role(request.user) != 'murid':
        return redirect('guru_dashboard')

    siswa = get_siswa_aktif(request.user)
    context = {
        'siswa': siswa,
        'rekening_list': RekeningBank.objects.filter(aktif=True),
        'base_template': 'portal/dashboardmurid.html',
        'tampilan': 'murid',
    }
    if siswa:
        context['tagihan_list'] = siswa.tagihan_spp.all()
    return render(request, 'pembayaran/riwayat_spp.html', context)


@login_required
def pembayaran_anak(request):
    if get_role(request.user) != 'orang_tua':
        return redirect('murid_dashboard')

    orangtua = getattr(request.user, 'orangtua', None)
    context = {
        'rekening_list': RekeningBank.objects.filter(aktif=True),
        'base_template': 'portal/dashboardortu.html',
        'tampilan': 'ortu',
    }
    if not orangtua:
        return render(request, 'pembayaran/riwayat_spp.html', context)

    siswa, daftar_anak = get_anak_aktif(request, orangtua)
    context['daftar_anak'] = daftar_anak
    context['siswa'] = siswa
    if siswa:
        context['tagihan_list'] = siswa.tagihan_spp.all()
    return render(request, 'pembayaran/riwayat_spp.html', context)
