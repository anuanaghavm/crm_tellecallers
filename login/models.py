from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from roles.models import Role

class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, role=None):
        if not email:
            raise ValueError("Users must have an email")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role)
        user.set_password(password)
        user.raw_password = password  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        from roles.models import Role
        admin_role, _ = Role.objects.get_or_create(name="Admin")
        return self.create_user(email=email, password=password, role=admin_role)

class Account(AbstractBaseUser):
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=128)
    raw_password = models.CharField(max_length=128, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    objects = AccountManager()
    USERNAME_FIELD = 'email'

    def _str_(self):
        return self.email