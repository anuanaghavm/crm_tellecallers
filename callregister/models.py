from django.db import models
from lead.models import Enquiry
from tellecaller.models import Telecaller
# Create your models here.
class CallRegister(models.Model):
    CALL_TYPE_CHOICES = [
        ('Incoming', 'Incoming'),
        ('Outgoing', 'Outgoing'),
    ]
    
    CALL_STATUS_CHOICES = [
        ('contacted', 'contacted'),
        ('Not Answered', 'Not Answered'),
        ('Busy', 'Busy'),
        ('Switched Off', 'Switched Off'),
        ('answered','Answered'),
        ('No Response', 'No Response'),
        ('Invalid Number', 'Invalid Number'),
        ('not_contacted', 'not_contacted'),

    ]
    
    CALL_OUTCOME_CHOICES = [
        ('Interested', 'Interested'),
        ('Not Interested', 'Not Interested'),
        ('Callback Requested', 'Callback Requested'),
        ('Information Provided', 'Information Provided'),
        ('Follow Up', 'Follow Up'),
        ('Converted', 'Converted'),
        ('Do Not Call', 'Do Not Call'),
        ('walk_in_list', 'walk_in_list'),
        ('closed', 'closed'),
    ]

    enquiry = models.ForeignKey(Enquiry, on_delete=models.CASCADE, related_name='call_logs')
    telecaller = models.ForeignKey(Telecaller, on_delete=models.CASCADE, related_name='call_logs')
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES, default='Outgoing')
    call_status = models.CharField(max_length=20, choices=CALL_STATUS_CHOICES)
    call_outcome = models.CharField(max_length=30, choices=CALL_OUTCOME_CHOICES, blank=True, null=True)
    
    call_duration = models.PositiveIntegerField(help_text="Duration in seconds", blank=True, null=True)
    call_start_time = models.DateTimeField(blank=True, null=True)
    call_end_time = models.DateTimeField(blank=True, null=True)
    
    notes = models.TextField(blank=True, null=True, help_text="Call notes and remarks")
    follow_up_date = models.DateField(blank=True, null=True)
    next_action = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Call Register'
        verbose_name_plural = 'Call Registers'

    def __str__(self):
        return f"{self.telecaller.name} - {self.enquiry.candidate_name} - {self.call_start_time}"

    def save(self, *args, **kwargs):
        # Calculate duration if both start and end times are provided
        if self.call_start_time and self.call_end_time:
            duration = (self.call_end_time - self.call_start_time).total_seconds()
            self.call_duration = int(duration)
        super().save(*args, **kwargs)



