from django.urls import path
from . import views

urlpatterns = [

    path(
        "guru/materi/",
        views.kelola_materi,
        name="kelola_materi"
    ),

    path(
        "guru/materi/tambah/",
        views.tambah_materi,
        name="tambah_materi"
    ),

    path(
        "guru/materi/edit/<int:id>/",
        views.edit_materi,
        name="edit_materi"
    ),

    path(
        "guru/materi/hapus/<int:id>/",
        views.hapus_materi,
        name="hapus_materi"
    ),

    # ===========================
    # MURID
    # ===========================

    path(
        "materi/",
        views.daftar_materi,
        name="daftar_materi"
    ),

]