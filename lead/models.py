# enquiry/models.py

from django.db import models
from branch.models import Branch
from login.models import Account
from tellecaller.models import Telecaller

class Mettad(models.Model):
    name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class checklist(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Service(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Enquiry(models.Model): 
    ENQUIRY_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Not interested', 'Not interested'),
    ]

    candidate_name = models.CharField(max_length=255)
    Mettad = models.ForeignKey(Mettad, on_delete=models.CASCADE, related_name='enquiries', null=True, blank=True)
    phone = models.CharField(max_length=15)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField()
    checklist = models.ManyToManyField(checklist, blank=True, related_name='enquiries')
    # Updated fields to use ForeignKey relationships
    preferred_course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    required_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='enquiries')
    
    enquiry_status = models.CharField(max_length=20, choices=ENQUIRY_STATUS_CHOICES, default='Active')
    feedback = models.TextField(blank=True, null=True)
    follow_up_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_enquiries')
    assigned_by = models.ForeignKey(Telecaller, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_enquiries')

    def __str__(self):
        return self.candidate_name