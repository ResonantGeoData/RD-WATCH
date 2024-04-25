from django.db import models


class Performer(models.Model):
    id = models.SmallAutoField(primary_key=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.slug
