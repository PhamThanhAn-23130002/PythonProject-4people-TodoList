from django.shortcuts import render
from django.http import HttpResponse

def create_board(request):
    return render(request, 'boards/BangCVcuaToi.html')