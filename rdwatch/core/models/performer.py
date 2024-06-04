from django.db import models


class Performer(models.Model):
    id = models.SmallAutoField(primary_key=True)
    short_code = models.SlugField(unique=True)
    team_name = models.TextField()

    def __str__(self):
        return self.short_code
