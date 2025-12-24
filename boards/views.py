from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Board, BoardMember, User
from django.contrib import messages # Để thông báo lỗi/thành công
from django.http import HttpResponse, request, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from tasks.models import Task
import json


def create_board(request):
    return render(request, "boards/BangCVcuaToi.html")


def card_detail(request):
    return render(request, "boards/CardDetail.html")


def home_page(request):
    return render(request, "boards/TrangChu.html")


def home_page2(request):
    return render(request, "boards/TrangChu2.html")


def home_page_Table(request):
    return render(request, "boards/TrangChu-Bang.html")

def log_out(request):
    return render(request, "accounts/login.html")

def about_me(request):
    return render(request, "accounts/SitePersonal.html")

# 1. Hiển thị trang chủ và danh sách Board
@login_required(login_url='/login/')
def home_page(request):
    boards = Board.objects.filter(owner=request.user).order_by('-created_at')
    
    context = {
        'boards': boards
    }
    return render(request, "boards/TrangChu.html", context)

# 2. Xử lý logic tạo Board mới
@login_required(login_url='/login/')
def create_board(request):
    if request.method == "POST":
        board_name = request.POST.get('title') 
        board_visibility = request.POST.get('visibility')

        if board_name:

            new_board = Board.objects.create(
                name=board_name,
                visibility=board_visibility,
                owner=request.user, 
                description=""
            )
            
            BoardMember.objects.create(
                project=new_board,
                user=request.user,
                role='admin'
            )
            return redirect('home_page')
    
   
    return redirect('home_page')


def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    members = BoardMember.objects.filter(project=board)

    session_key = f"board_{board_id}_lists"
    lists = request.session.get(session_key, [])
    context = {
        'board': board,
        'members': members,
        'lists': lists,
    }
    return render(request, "boards/BangCVcuaToi.html", context) 

# 2. Hàm xử lý thêm thành viên bằng Email
def add_member(request, board_id):
    if request.method == "POST":
        board = get_object_or_404(Board, id=board_id)
        email = request.POST.get('email')
        
        try:
            user_to_add = User.objects.get(email=email)
            
            if BoardMember.objects.filter(project=board, user=user_to_add).exists():
                messages.warning(request, f'Thành viên {email} đã có trong bảng này!')
            else:
                BoardMember.objects.create(project=board, user=user_to_add, role='member')
                messages.success(request, f'Đã thêm {email} vào bảng thành công!')
                
        except User.DoesNotExist:
            messages.error(request, f'Không tìm thấy người dùng với email: {email}')
            
    return redirect('board_detail', board_id=board_id)



def delete_board(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    
    if request.user != board.owner:
        messages.error(request, "Bạn không có quyền xóa bảng này!")
        return redirect('board_detail', board_id=board_id)
    
    if request.method == "POST":
        board.delete()
        messages.success(request, "Đã xóa bảng thành công!")
        return redirect('home_page')
    return redirect('home_page')



@csrf_exempt
def save_board_session(request, board_id):
    #Lưu danh sách + thẻ tạm thời vào session (chưa DB)
    if request.method == "POST":
        data = json.loads(request.body)

        # key session theo từng board
        session_key = f"board_{board_id}_lists"

        request.session[session_key] = data.get("lists", [])
        request.session.modified = True

        return JsonResponse({"status": "ok"})


#-----------------------------------------------------------thêm----------------------------------------
def createdealine(request):
 if request.method == "POST":
    d1 = request.POST.get("title")
    d2 = request.POST.get("description")
    d3 = request.POST.get("priority")
    d4 = request.POST.get("process")
    d5 = request.POST.get("complexity")
    d6 = request.POST.get("inputdate")
    Task.objects.create(
        title = d1,
        description = d2,
        priority = d3, 
        status = d4,
        difficulty =d5,
        deadline =d6)













