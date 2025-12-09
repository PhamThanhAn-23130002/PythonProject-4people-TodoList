from django.db import models

# Create your models here.
class User(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    username = models.CharField(max_length=30)
    password = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)

class Skill(models.Model):
    id = models.CharField(max_length=10 , primary_key=True)
    name = models.CharField(max_length=50)
  
class UserProfile(models.Model):
    id = models.CharField(max_length=10 , primary_key=True)
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length= 200)
    experience_level = models.CharField(max_length=10)
    skill = models.ManyToManyField(Skill)
    role = models.CharField(max_length=10)
