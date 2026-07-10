from django.urls import path
from . import views

urlpatterns = [
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("guru-dashboard/", views.guru_dashboard, name="guru_dashboard"),
    path("dashboard/", views.murid_dashboard, name="murid_dashboard"),
    path("buka-quiz/", views.buka_quiz, name="buka_quiz"),
]