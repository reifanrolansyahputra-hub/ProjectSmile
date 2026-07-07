from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Project


@login_required
def admin_dashboard(request):
    return render(request, "portal/admin_dashboard.html")


@login_required
def guru_dashboard(request):

    projects = Project.objects.filter(is_active=True)

    return render(request, "portal/guru_dashboard.html", {
        "projects": projects
    })


@login_required
def murid_dashboard(request):

    projects = Project.objects.filter(is_active=True)

    return render(request, "portal/dashboard.html", {
        "projects": projects
    })