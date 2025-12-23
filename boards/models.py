from django.db import models
from accounts.models import User
import uuid

class Board(models.Model):
    name = models.CharField(max_length=50)
    VISIBILITY_CHOICES = [
        ('workspace', 'Không gian làm việc'),
        ('private', 'Riêng tư'),
        ('public', 'Công khai'),
    ]
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='workspace')
    description = models.TextField(max_length=200, blank=True, null=True) 
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    #Tạo mã chia sẻ ngẫu nhiên, không trùng lặp
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return self.name

class BoardMember(models.Model):
    project = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default="member") 
    joined_at = models.DateTimeField(auto_now_add=True)