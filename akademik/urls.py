from django.urls import path

from . import views

urlpatterns = [
    # ===== GURU =====
    path('guru/absensi/', views.pilih_kelas_absensi, name='pilih_kelas_absensi'),
    path('guru/absensi/<int:kelas_id>/', views.absen_kelas, name='absen_kelas'),

    path('guru/tugas/', views.daftar_tugas, name='daftar_tugas'),
    path('guru/tugas/tambah/', views.tambah_tugas, name='tambah_tugas'),
    path('guru/tugas/edit/<int:id>/', views.edit_tugas, name='edit_tugas'),
    path('guru/tugas/hapus/<int:id>/', views.hapus_tugas, name='hapus_tugas'),
    path('guru/tugas/<int:tugas_id>/nilai/', views.input_nilai, name='input_nilai'),

    path('guru/ranking/', views.pilih_kelas_ranking, name='pilih_kelas_ranking'),
    path('guru/ranking/<int:kelas_id>/', views.lihat_ranking_guru, name='lihat_ranking_guru'),

    # ===== MURID =====
    path('murid/absensi/', views.absensi_saya, name='absensi_saya'),
    path('murid/nilai/', views.nilai_saya, name='nilai_saya'),
    path('murid/ranking/', views.ranking_saya, name='ranking_saya'),

    # ===== ORANG TUA =====
    path('ortu/absensi/', views.absensi_anak, name='absensi_anak'),
    path('ortu/nilai/', views.nilai_anak, name='nilai_anak'),
    path('ortu/ranking/', views.ranking_anak, name='ranking_anak'),
]
