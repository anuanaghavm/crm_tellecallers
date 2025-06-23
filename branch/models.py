from django.db import models

class Branch(models.Model):

    branch_name = models.CharField(max_length=255)  # Branch Name
    address = models.TextField()  # Address
    city = models.CharField(max_length=100)  # City
    state = models.CharField(max_length=100)  # State
    country = models.CharField(max_length=100)  # Country
    email = models.EmailField(unique=True)  # Email
    contact = models.CharField(max_length=15)  # Contact
    

    def __str__(self):
        return self.branch_name

