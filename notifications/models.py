from django.db import models
from boards.models import Board
from accounts.models import User
from boards.models import Card

class BoardShare(models.Model):
    ROLE_CHOICES = [
        ("viewer", "Viewer"),
        ("editor", "Editor"),
        ("owner", "Owner"),
    ]

    project = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="viewer")

    invited_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('project', 'user')

class Notification(models.Model):
    TYPE_CHOICES = [
        ("reminder", "Reminder"),
        ("deadline", "Deadline Approaching"),
        ("overdue", "Overdue"),
        ("assigned", "Task Assigned"),
        ("general", "General Notification"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True, blank=True)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


