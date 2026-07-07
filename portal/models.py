from django.db import models

class Project(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField()

    url = models.URLField()

    image = models.ImageField(upload_to="project_icons/")

    category = models.CharField(max_length=50)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    