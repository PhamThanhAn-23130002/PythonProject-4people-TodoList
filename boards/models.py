from django.db import models
from accounts.models import User

# Create your models here.
class Board(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200)
    owner_id = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)

class BoardMember(models.Model):
    project = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default="member") 
    joined_at = models.DateTimeField(auto_now_add=True)