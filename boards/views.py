from django.shortcuts import render
from django.http import HttpResponse

def create_board(request):
    return render(request, 'boards/BangCVcuaToi.html')

def card_detail(request):
    return render(request, 'boards/CardDetail.html')


def home_page(request):
    return render(request, 'boards/TrangChu.html')

def home_page2(request):
    return render(request, 'boards/TrangChu2.html')

def home_page_Table(request):
    return render(request, 'boards/TrangChu-Bang.html')


