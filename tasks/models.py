from django.db import models
from boards.models import Board
from accounts.models import User

# Create your models here.
    
class List(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    board_id = models.OneToOneField(Board, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    position = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
class Task(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    list_id = models.ForeignKey(List, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    description = models.TextField(max_length=200)
    priority = models.TextField(max_length=10)
    status = models.BooleanField(default=True)
    difficulty = models.CharField(max_length=10)
    assignee_id =models.CharField(max_length=10)
    reporter_id =models.CharField(max_length=10)
    deadline = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(auto_now=True)
    createed_at =models.DateTimeField(auto_now_add=True)
    update_at =models.DateTimeField(auto_now_add=True)
    
class Tag(models.Model):
    tasks = models.ManyToManyField(Task, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10)
    
class Checklist(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    task_id = models.OneToOneField(Task, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    
class ChecklistItem(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    checklist_id = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    is_completed = models.BooleanField(default=True)  
    
class Comment(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    task_id = models.ForeignKey(Task, on_delete=models.CASCADE)
    author_id = models.ForeignKey(User, on_delete=models.CASCADE) 
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    