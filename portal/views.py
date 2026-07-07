from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Project
from materi.models import Materi


@login_required
def admin_dashboard(request):
    return render(request, "portal/admin_dashboard.html")


@login_required
def guru_dashboard(request):

    projects = Project.objects.filter(is_active=True)

    materis = Materi.objects.filter(
        guru=request.user
    ).order_by("-created_at")

    return render(request, "portal/guru_dashboard.html", {
        "projects": projects,
        "materis": materis
    })


@login_required
def murid_dashboard(request):

    projects = Project.objects.filter(is_active=True)

    # Ambil SEMUA materi dari semua guru
    materis = Materi.objects.all().order_by("-created_at")

    return render(request, "portal/dashboard.html", {
        "projects": projects,
        "materis": materis
    })