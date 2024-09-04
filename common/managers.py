from django.db import models


class RegionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(parent__isnull=True)

class DistrictManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(parent__isnull=False)