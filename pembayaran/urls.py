from django.urls import path

from . import views

urlpatterns = [
    # ===== ADMIN =====
    path('admin-sekolah/spp/', views.kelola_spp, name='kelola_spp'),
    path('admin-sekolah/spp/generate/', views.generate_tagihan, name='generate_tagihan'),
    path('admin-sekolah/spp/<int:tagihan_id>/bayar/', views.catat_pembayaran, name='catat_pembayaran'),
    path('admin-sekolah/rekening/tambah/', views.tambah_rekening, name='tambah_rekening'),
    path('admin-sekolah/rekening/<int:id>/toggle/', views.toggle_rekening, name='toggle_rekening'),
    path('admin-sekolah/rekening/<int:id>/hapus/', views.hapus_rekening, name='hapus_rekening'),

    # ===== MURID & ORANG TUA =====
    path('murid/pembayaran/', views.pembayaran_murid, name='pembayaran_murid'),
    path('ortu/pembayaran/', views.pembayaran_anak, name='pembayaran_anak'),
]
