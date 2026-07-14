from django.db import models
from django.contrib.auth.models import User


class Materi(models.Model):

    MAPEL_CHOICES = [
        ("MTK", "Matematika"),
        ("IPA", "IPA"),
        ("IPS", "IPS"),
        ("BIO", "Biologi"),
        ("FIS", "Fisika"),
        ("KIM", "Kimia"),
        ("ING", "Bahasa Inggris"),
        ("IND", "Bahasa Indonesia"),
    ]

    KELAS_CHOICES = [
        (1, "Kelas 1"),
        (2, "Kelas 2"),
        (3, "Kelas 3"),
        (4, "Kelas 4"),
        (5, "Kelas 5"),
        (6, "Kelas 6"),
    ]

    judul = models.CharField(max_length=200)

    mapel = models.CharField(
        max_length=10,
        choices=MAPEL_CHOICES
    )

    kelas = models.IntegerField(
        choices=KELAS_CHOICES,
        default=1
    )

    deskripsi = models.TextField()

    guru = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to="materi/"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.judul