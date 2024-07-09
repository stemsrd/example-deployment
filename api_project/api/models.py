from django.db import models

class ScraperResult(models.Model):
    name = models.CharField(max_length=255)
    userid = models.CharField(max_length=255)
    url = models.URLField()
    registration_number = models.CharField(max_length=255, null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True)
    name_used_in_practice = models.CharField(max_length=255, null=True, blank=True)
    registrant_type = models.CharField(max_length=255, null=True, blank=True)
    languages_of_care = models.TextField(null=True, blank=True)
    registration_status = models.CharField(max_length=255, null=True, blank=True)
    areas_of_practice = models.TextField(null=True, blank=True)
    # Add more fields as needed

    def __str__(self):
        return f"{self.name} ({self.userid})"