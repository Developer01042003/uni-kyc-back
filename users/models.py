from django.contrib.auth.models import AbstractUser
from django.db import models
from company.models import *
import uuid

class User(AbstractUser):
    full_name = models.CharField(max_length=50,blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    address = models.TextField()
    country = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_banned = models.BooleanField(default=False)
    is_kyc = models.BooleanField(default=False)
    is_nft = models.BooleanField(default=False)

    def __str__(self):
        return self.email
    

class sharedData(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True,unique=True,editable=False)
    company = models.ForeignKey(Company,on_delete=models.CASCADE) 