from django.db import models

# Create your models here.
from tellecaller.models import Telecaller  # Adjust this import path as needed

class Lead(models.Model):
    SOURCE_CHOICES = [
        ('Manual', 'Manual'),
        ('Meta', 'Meta'),
        ('Google', 'Google'),
    ]
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Follow-up', 'Follow-up'),
        ('Converted', 'Converted'),
        ('Closed', 'Closed')
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    notes = models.TextField(blank=True, null=True)
    follow_up = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    telecaller = models.ForeignKey(
        Telecaller,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )

    def __str__(self):
        return self.name
