from django.shortcuts import render
from django.http import HttpResponse

def create_board(request):
    return render(request, 'boards/BangCVcuaToi.html')
def trang_chu(request):
    return render(request, 'boards/TrangChu.html')