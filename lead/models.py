from django.db import models
from django.utils.timezone import now
from tellecaller.models import Telecaller  # External model import — safe here

from datetime import date  # Add this import

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
        ('Closed', 'Closed'),
        ('Make_a_call', 'Make a Call'),
        ('Fix Walk in', 'Fix Walk in'),
        ('insterested', 'Interested'),
        ('Not Interested', 'Not Interested'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')

    # For follow-up
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_remarks = models.TextField(null=True, blank=True)

    # For walk-in
    walk_in_date = models.DateField(null=True, blank=True)
    walk_in_remark = models.TextField(null=True, blank=True)

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


class CallRegister(models.Model):
    CALL_STATUS_CHOICES = [
        ('Answered', 'Answered'),
        ('Missed', 'Missed'),
        ('Rejected', 'Rejected'),
        ('Follow-up', 'Follow-up'),
    ]
    RESPOND_TYPE_CHOICES = [
        ('Positive', 'Positive'),
        ('Negative', 'Negative'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='calls')
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES)
    call_time = models.DateTimeField()
    call_date = models.DateField(default=date.today)
    duration = models.CharField(max_length=10, blank=True, null=True)  # e.g., "00:03:45"
    respond_type = models.CharField(max_length=10, choices=RESPOND_TYPE_CHOICES)
    responds = models.CharField(max_length=255)  # e.g., "Appointment Fixed"
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call with {self.lead.name} on {self.call_date}"
