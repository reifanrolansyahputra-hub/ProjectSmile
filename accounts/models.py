from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('guru', 'Guru'),
        ('murid', 'Murid'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='murid'
    )

    def __str__(self):
        return self.user.username