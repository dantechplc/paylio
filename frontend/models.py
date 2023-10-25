from django.db import models

# Create your models here.

class CompanyProfile(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    company_address = models.TextField(max_length=500)
    company_logo = models.ImageField(upload_to="company_profile")
    favicon = models.ImageField(upload_to="company_profile")
    support_email = models.EmailField(max_length=200)
    forwarding_email = models.EmailField(max_length=200)

    def __str__(self):
        return self.name