from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

# Create your models here.
class User(AbstractUser):
    pass

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


class EmailOTP(models.Model):
    email = models.EmailField(unique=True, null=False, blank=False)
    otp = models.CharField(max_length=6, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """
        Kiểm tra xem OTP còn hiệu lực không.
        Mặc định set là 5 phút (300 giây).
        """
        lifespan = datetime.timedelta(minutes=5)
        now = timezone.now()

        return now - self.created_at < lifespan

    def __str__(self):
        return f"{self.email} - {self.otp}"
