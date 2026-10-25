import time
import jwt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from .models import Project
from materi.models import Materi
from accounts.models import Profile
from accounts.utils import get_anak_aktif, get_role
from akademik.models import Kelas, Siswa
from pembayaran.models import TagihanSPP

ROLE_DASHBOARD_URL = {
    'admin': 'admin_dashboard',
    'guru': 'guru_dashboard',
    'murid': 'murid_dashboard',
    'orang_tua': 'orangtua_dashboard',
}


def _redirect_ke_dashboard_sendiri(user):
    role = get_role(user)
    return redirect(ROLE_DASHBOARD_URL.get(role, 'home'))


# Pemetaan role Django -> role yang dikenal Quiz GAME (Live Puzzle Game)
GAME_ROLE_MAP = {
    "admin": "guru",
    "guru": "guru",
    "murid": "murid",
}
# Pemetaan role Django -> role yang dikenal quiz (quiz cuma punya 'guru' & 'murid')
QUIZ_ROLE_MAP = {
    "admin": "guru",
    "guru": "guru",
    "murid": "murid",
}


@login_required
def admin_dashboard(request):
    if get_role(request.user) != "admin":
        return _redirect_ke_dashboard_sendiri(request.user)

    sekarang = timezone.localdate()

    tagihan_bulan_ini = list(
        TagihanSPP.objects.filter(bulan=sekarang.month, tahun=sekarang.year)
    )
    jumlah_lunas = sum(1 for t in tagihan_bulan_ini if t.status == "Lunas")

    stats = {
        "jumlah_kelas": Kelas.objects.count(),
        "jumlah_siswa": Siswa.objects.filter(aktif=True).count(),
        "jumlah_guru": Profile.objects.filter(role="guru").count(),
        "jumlah_ortu": Profile.objects.filter(role="orang_tua").count(),
        "tagihan_bulan_ini": len(tagihan_bulan_ini),
        "tagihan_lunas": jumlah_lunas,
        "tagihan_belum_lunas": len(tagihan_bulan_ini) - jumlah_lunas,
    }

    nama_bulan = dict(TagihanSPP.BULAN_CHOICES).get(sekarang.month, "")

    return render(request, "portal/dashboard.html", {
        "stats": stats,
        "kelas_list": Kelas.objects.all().order_by("tingkat", "nama"),
        "nama_bulan_tahun_ini": f"{nama_bulan} {sekarang.year}",
    })


@login_required
def guru_dashboard(request):
    if get_role(request.user) not in ("admin", "guru"):
        return _redirect_ke_dashboard_sendiri(request.user)

    projects = Project.objects.filter(is_active=True)
    materis = Materi.objects.filter(
        guru=request.user
    ).order_by("-created_at")

    return render(request, "portal/guru_dashboard.html", {
        "projects": projects,
        "materis": materis,
        "QUIZ_APP_URL": settings.QUIZ_APP_URL,
    })


@login_required
def murid_dashboard(request):
    if get_role(request.user) != "murid":
        return _redirect_ke_dashboard_sendiri(request.user)

    projects = Project.objects.filter(is_active=True)
    
    # Ambil SEMUA materi dari semua guru
    materis = Materi.objects.all().order_by("-created_at")

    # === DIUBAH DI SINI: Sekarang memanggil file html khusus milik murid ===
    return render(request, "portal/dashboardmurid.html", {
        "projects": projects,
        "materis": materis,
        "QUIZ_APP_URL": settings.QUIZ_APP_URL,
    })


@login_required
def orangtua_dashboard(request):
    if get_role(request.user) != "orang_tua":
        return _redirect_ke_dashboard_sendiri(request.user)

    projects = Project.objects.filter(is_active=True)
    orangtua = getattr(request.user, "orangtua", None)

    siswa_aktif, daftar_anak = None, []
    if orangtua:
        siswa_aktif, daftar_anak = get_anak_aktif(request, orangtua)

    return render(request, "portal/dashboardortu.html", {
        "projects": projects,
        "orangtua": orangtua,
        "siswa_aktif": siswa_aktif,
        "daftar_anak": daftar_anak,
    })


@login_required
def buka_quiz(request):
    """
    Menerbitkan token SSO singkat (60 detik) lalu mengarahkan user ke
    Quiz App (Node.js) dengan token itu di query string. Quiz App akan
    menukar token ini dengan token sesi quiz miliknya sendiri.
    """
    try:
        profile = Profile.objects.get(user=request.user)
        role_django = profile.role
    except Profile.DoesNotExist:
        role_django = "murid"

    role_quiz = QUIZ_ROLE_MAP.get(role_django, "murid")

    payload = {
        "username": request.user.username,
        "fname": request.user.first_name or request.user.username,
        "lname": request.user.last_name or "-",
        "role": role_quiz,
        "sso": True,
        "exp": int(time.time()) + 60,  # token ini sengaja cuma valid 60 detik
    }
    token = jwt.encode(payload, settings.SSO_SHARED_SECRET, algorithm="HS256")

    return redirect(f"{settings.QUIZ_APP_URL}/?ssoToken={token}")

@login_required
def buka_quiz_game(request):
    """
    SSO ke Quiz GAME (Live Puzzle Game) — project TERPISAH dari Quiz
    Pelajaran di atas: game berbasis HTML/JS statis + backend Flask
    (server.py), bukan Node.js. Token singkat (60 detik) dikirim lewat
    query string ?ssoToken=..., lalu diverifikasi oleh server.py.
    """
    try:
        profile = Profile.objects.get(user=request.user)
        role_django = profile.role
    except Profile.DoesNotExist:
        role_django = "murid"

    role_game = GAME_ROLE_MAP.get(role_django, "murid")

    payload = {
        "username": request.user.username,
        "fname": request.user.first_name or request.user.username,
        "lname": request.user.last_name or "-",
        "role": role_game,
        "sso": True,
        "exp": int(time.time()) + 60,
    }
    token = jwt.encode(payload, settings.GAME_SSO_SHARED_SECRET, algorithm="HS256")

    return redirect(f"{settings.GAME_APP_URL}?ssoToken={token}")