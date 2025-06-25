from django.db import models

class Role(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Telecaller', 'Telecaller'),
        # ('Branch Manager', 'Branch Manager'),
    ]
    
    name = models.CharField(max_length=50,choices=ROLE_CHOICES)

    def __str__(self):
        return self.name
