from django.db import models
from roles.models import Role
from login.models import Account
from branch.models import Branch
from django.utils.timezone import now

class Telecaller(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="telecaller_user")
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(default=now)
    status = models.CharField(max_length=30, choices=[('active', 'Active'), ('deactivated', 'Deactivated')], default='active')
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_telecallers")

    def __str__(self):
        return self.name
