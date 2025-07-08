from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from roles.models import Role

class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, role=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.raw_password = password  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        from roles.models import Role
        admin_role, _ = Role.objects.get_or_create(name="Admin")
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, password=password, role=admin_role, **extra_fields)

class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=128)
    raw_password = models.CharField(max_length=128, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # <== Needed for admin access
    is_superuser = models.BooleanField(default=False)  # <== Needed for superuser

    objects = AccountManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
