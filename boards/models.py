# boards/models.py
from django.db import models
from accounts.models import User
import uuid
from django.utils import timezone

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
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return self.name

class BoardMember(models.Model):
    project = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

class List(models.Model):
    board = models.ForeignKey(Board, related_name="lists", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Card(models.Model):
    list = models.ForeignKey(List, related_name="cards", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    # --- CÁC TRƯỜNG PHỤC VỤ AI VÀ CHI TIẾT ---
    description = models.TextField(default="", blank=True) # Mô tả công việc
    required_skills = models.TextField(default="", blank=True, help_text="Kỹ năng yêu cầu") # AI sẽ đọc cái này
    deadline = models.DateTimeField(null=True, blank=True)
    
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, related_name='cards', blank=True)
    is_completed = models.BooleanField(default=False)
    @property
    def is_overdue(self):
        # Nếu có deadline VÀ deadline nhỏ hơn giờ hiện tại VÀ chưa hoàn thành
        if self.deadline and self.deadline < timezone.now() and not self.is_completed:
            return True
        return False

    def __str__(self):
        return self.title

class Checklist(models.Model):
    # Liên kết với Card của app boards
    card = models.ForeignKey(Card, related_name="checklists", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, related_name="items", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title