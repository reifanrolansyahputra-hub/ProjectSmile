import time
import jwt
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Project
from materi.models import Materi
from accounts.models import Profile

# Pemetaan role Django -> role yang dikenal quiz (quiz cuma punya 'guru' & 'murid')
QUIZ_ROLE_MAP = {
    "admin": "guru",
    "guru": "guru",
    "murid": "murid",
}


@login_required
def admin_dashboard(request):
    return render(request, "portal/dashboard.html")


@login_required
def guru_dashboard(request):
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