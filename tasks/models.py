# tasks/models.py
from django.db import models
from accounts.models import User
from boards.models import Card # Import Card từ app boards sang

class Tag(models.Model):
    # Một thẻ Card có thể có nhiều Tag, một Tag có thể gắn nhiều Card
    cards = models.ManyToManyField(Card, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10)

    def __str__(self):
        return self.name

class Comment(models.Model):
    # Comment gắn vào Card
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE) 
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.card.title}"