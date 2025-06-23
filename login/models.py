from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from roles.models import Role

class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, role=None):
        if not email:
            raise ValueError("The Email field must be set")
        user = self.model(email=self.normalize_email(email), password=password)  # Store plain text password
        if role:
            user.role = role
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        from roles.models import Role  # Import here to prevent circular imports
        admin_role, _ = Role.objects.get_or_create(name="Admin")
        user = self.create_user(email=email, password=password, role=admin_role)
        return user

class Account(AbstractBaseUser):
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=128)  # Store password as plain text
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    objects = AccountManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
