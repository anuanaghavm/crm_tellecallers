# enquiry/models.py

from django.db import models
from branch.models import Branch
class Enquiry(models.Model):
    ENQUIRY_SOURCE_CHOICES = [
        ('Google', 'Google'),
        ('Facebook', 'Facebook'),
        ('Instagram', 'Instagram'),
        ('Referral', 'Referral'),    ] 
    ENQUIRY_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Closed', 'Closed'),
        ('Follow Up', 'Follow Up'),
        ('Not Interested', 'Not Interested'),
        ('Converted', 'Converted'),
        ('interested','interested'),
        ('contacted','contacted'),
        ('walk_in_list','walk_in_list'),
        ]
    candidate_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    telecaller = models.ForeignKey('tellecaller.Telecaller', on_delete=models.SET_NULL, null=True, blank=True)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()
    enquiry_source = models.CharField(max_length=100, choices=ENQUIRY_SOURCE_CHOICES)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_course = models.CharField(max_length=255)
    enquiry_status = models.CharField(max_length=20, choices=ENQUIRY_STATUS_CHOICES, default='Active')
    required_service = models.CharField(max_length=255)
    feedback = models.TextField(blank=True, null=True)
    follow_up_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('login.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_enquiries')

    def __str__(self):
        return self.candidate_name


