from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
)
from django.core.validators import RegexValidator, validate_email
from django.conf import settings


phone_regex = RegexValidator(
    regex=r"^\d{10}", message="Phone number must be 10 digits only."
)

class UserManager(BaseUserManager):
    """
    User Manager.
    To create superuser.
    """

    def create_user(self, username, first_name, last_name, email=None, password=None, otp_verify=False, is_superuser=False):
        if not username:
            raise ValueError("Users must have a username")
        if not first_name and is_superuser==False:
            raise ValueError("Users must have a first name")
        if not last_name and is_superuser==False:
            raise ValueError("Users must have a last name")
        

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            telephone_number="",
            email=email,
            is_active=True
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username, password):
        user = self.create_user(
            username=username, password=password,
            first_name="", last_name= "" , is_superuser=True
        )
        # user.is_active = True
        user.is_verify = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class UserModel(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.
    """
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    telephone_number = models.CharField(
        max_length=20, null=True, blank=True #, validators=[phone_regex]
    )

    email = models.EmailField(
        max_length=50,
        blank=True,
        null=True,
        validators=[validate_email],
    )

    is_verify = models.BooleanField(default=False) # If the account is verify

    is_active = models.BooleanField(default=False) # If the account is active
    is_staff = models.BooleanField(default=False)
    user_registered_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'


    def get_full_name(self):
        return self.first_name + " " + self.last_name
        
    def __str__(self):
        return self.username

class Address(models.Model):
    country = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return f"{self.country} {self.city}"

class UserProfile(models.Model):
    user = models.OneToOneField(
        UserModel,
        related_name="userprofile",
        on_delete=models.CASCADE,
        primary_key=True,
    )

    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"Profile of {self.user.username}"


class OTPRequest(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    expiry_time = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    purpose = models.CharField(max_length=30, choices=[('register', 'Register'), ('reset_password', 'Reset Password')])

    def __str__(self):
        return f"OTP for {self.user.email} (used: {self.used}, purpose: {self.purpose})"
