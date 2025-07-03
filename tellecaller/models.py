from django.db import models
from login.models import Account
from roles.models import Role
from django.utils.timezone import now
from branch.models import Branch

class Telecaller(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True) 
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=15)
    
    address = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('deactivated', 'Deactivated')], default='active')
    created_date = models.DateTimeField(default=now)
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_telecallers')

    def __str__(self):
        return self.name
