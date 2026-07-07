from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Materi


@login_required
def kelola_materi(request):

    materis = Materi.objects.filter(
        guru=request.user
    ).order_by("-created_at")

    return render(
        request,
        "materi/kelola_materi.html",
        {
            "materis": materis
        }
    )


@login_required
def tambah_materi(request):

    if request.method == "POST":

        Materi.objects.create(
            judul=request.POST.get("judul"),
            mapel=request.POST.get("mapel"),
            deskripsi=request.POST.get("deskripsi"),
            file=request.FILES.get("file"),
            guru=request.user
        )

    return redirect("kelola_materi")


@login_required
def edit_materi(request, id):

    materi = get_object_or_404(
        Materi,
        id=id,
        guru=request.user
    )

    if request.method == "POST":

        materi.judul = request.POST.get("judul")
        materi.mapel = request.POST.get("mapel")
        materi.deskripsi = request.POST.get("deskripsi")

        if request.FILES.get("file"):
            materi.file = request.FILES.get("file")

        materi.save()

        return redirect("kelola_materi")

    materis = Materi.objects.filter(
        guru=request.user
    ).order_by("-created_at")

    return render(
        request,
        "materi/kelola_materi.html",
        {
            "materis": materis,
            "edit_data": materi
        }
    )


@login_required
def hapus_materi(request, id):

    materi = get_object_or_404(
        Materi,
        id=id,
        guru=request.user
    )

    materi.delete()

    return redirect("kelola_materi")


# ===========================
# VIEW UNTUK MURID
# ===========================

@login_required
def daftar_materi(request):

    mapel = request.GET.get("mapel")
    guru = request.GET.get("guru")

    materis = Materi.objects.all().order_by("-created_at")

    if mapel:
        materis = materis.filter(mapel=mapel)

    if guru:
        materis = materis.filter(guru__username=guru)

    guru_list = (
        Materi.objects
        .values_list("guru__username", flat=True)
        .distinct()
    )

    return render(
        request,
        "materi/daftar_materi.html",
        {
            "materis": materis,
            "guru_list": guru_list,
            "mapel_aktif": mapel,
            "guru_aktif": guru,
        }
    )