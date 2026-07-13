from django.urls import path
from . import views

urlpatterns = [
    # Jalur lama bawaan login sistem kamu
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("guru-dashboard/", views.guru_dashboard, name="guru_dashboard"),
    path("buka-quiz/", views.buka_quiz, name="buka_quiz"),

    # === JALUR UTAMA PORTAL DASHBOARD (Disamakan namanya agar tidak error) ===
    path("dashboard/", views.admin_dashboard, name="dashboard_utama"),
    path("dashboard/guru/", views.guru_dashboard, name="guru_dashboard"), # Nama disamakan 'guru_dashboard'
    path("dashboard/murid/", views.murid_dashboard, name="murid_dashboard"), # Nama disamakan 'murid_dashboard'
]