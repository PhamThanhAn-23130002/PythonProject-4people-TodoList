from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Board, BoardMember, User
from django.contrib import messages # Để thông báo lỗi/thành công
from django.http import HttpResponse, request, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from tasks.models import Task
import json
from django.db.models import Q #phép tuyển
from .models import Board, List, Card,Checklist, ChecklistItem
from tasks.models import Task
from datetime import datetime
from django.utils import timezone
def create_board(request):
    return render(request, "boards/BangCVcuaToi.html")


def card_detail(request):
    return render(request, "boards/CardDetail.html")

# def card_detail_id(request, card_id):
#     card = get_object_or_404(Card, id=card_id)
#
#     return render(request, "boards/CardDetail.html", {
#         "card": card
#     })
def card_detail_id(request, card_id):
    card = get_object_or_404(Card, id=card_id)

    checklists = card.checklists.prefetch_related("items").all()

    return render(request, "boards/CardDetail.html", {
        "card": card,
        "checklists": checklists
    })


def home_page(request):
    return render(request, "boards/TrangChu.html")


def home_page2(request):
    return render(request, "boards/TrangChu2.html")


def home_page_Table(request):
    return render(request, "boards/TrangChu-Bang.html")


def about_me(request):
    return render(request, "accounts/SitePersonal.html")


def dismiss_intro(request):
    # Lưu vào session là đã tắt intro rồi
    request.session['intro_dismissed'] = True
    return redirect('home_page')


# 1. Hiển thị trang chủ và danh sách Board
@login_required(login_url='/login/')
def home_page(request):
    boards = Board.objects.filter(
        Q(owner=request.user) | Q(boardmember__user=request.user)
    ).distinct().order_by('-created_at')  # .distinct() giúp loại bỏ trùng lặp nếu lỡ bạn vừa là chủ vừa là thành viên
    
    # Kiểm tra xem người dùng đã tắt intro chưa (mặc định là False - tức là chưa tắt)
    # Nếu trong session có 'intro_dismissed' = True thì show_intro sẽ là False
    show_intro = not request.session.get('intro_dismissed', False)
    context = {
        'boards': boards,
        'show_intro': show_intro,
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


# def board_detail(request, board_id):
#     board = get_object_or_404(Board, id=board_id)
#     members = BoardMember.objects.filter(project=board)
#
#     all_boards = Board.objects.filter(
#         Q(owner=request.user) | Q(boardmember__user=request.user)
#     ).distinct().order_by('-created_at')
#
#     session_key = f"board_{board_id}_lists"
#     lists = request.session.get(session_key, [])
#     context = {
#         'board': board,
#         'members': members,
#         'lists': lists,
#         'all_boards': all_boards,
#     }
#     return render(request, "boards/BangCVcuaToi.html", context)
def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    members = BoardMember.objects.filter(project=board)

    lists = List.objects.filter(board=board).prefetch_related("cards").order_by("position")

    context = {
        "board": board,
        "members": members,
        "lists": lists,
        "all_boards": Board.objects.filter(owner=request.user)
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



def save_board_db(request, board_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    lists_data = data.get("lists", [])

    board = Board.objects.get(id=board_id)

    #  XÓA dữ liệu cũ (để sync lại theo frontend)
    List.objects.filter(board=board).delete()

    for list_index, l in enumerate(lists_data):
        list_obj = List.objects.create(
            board=board,
            title=l["title"],
            position=list_index
        )

        for card_index, card_title in enumerate(l["cards"]):
            Card.objects.create(
                list=list_obj,
                title=card_title,
                position=card_index
            )
            
    return JsonResponse({"status": "saved"})
    

def join_via_link(request, token):
    # Tìm bảng dựa trên token (chứ không phải ID)
    board = get_object_or_404(Board, share_token=token)
    
    # Nếu user chưa đăng nhập thì bắt đăng nhập trước
    if not request.user.is_authenticated:
        # (Chỗ này bạn có thể redirect sang trang login)
        return redirect('/login/') 
        
    # Kiểm tra xem đã là thành viên chưa
    if not BoardMember.objects.filter(project=board, user=request.user).exists():
        # Chưa thì thêm vào làm thành viên
        BoardMember.objects.create(project=board, user=request.user, role='member')
        messages.success(request, f"Bạn đã tham gia vào bảng {board.name} thành công!")
    else:
        messages.info(request, "Bạn đã là thành viên của bảng này rồi.")
        
    # Chuyển hướng vào trang chi tiết bảng
    return redirect('board_detail', board_id=board.id)

def createdealine(request):
 if request.method == "POST":
    d1 = request.POST.get("title")
    d2 = request.POST.get("description")
    d3 = request.POST.get("priority")
    d4 = request.POST.get("process")
    d5 = request.POST.get("complexity")
    d6 = request.POST.get("inputdate")
    d7 = request.POST.get("inputtime")
    dt = datetime.strptime(
            f"{d6} {d7}",
            "%Y-%m-%d %H:%M"
        )
    Task.objects.create(
        title = d1,
        description = d2,
        priority = d3, 
        status = d4,
        difficulty =d5,
        deadline = dt)
    return redirect("boards/BangCVcuaToi.html")
def loaddealine(request,id):
    list=Task.objects.get(id==id)
    dealine = list.deadline
    if timezone.is_aware(dealine):
        dealine = timezone.localtime(dealine)
    context={
        "deadline_date": dealine.date(),
        "deadline_time": dealine.time().strftime("%H:%M"),
        
    }
    return render(request, "CardDetail.html", context)
def detail_task(request, id):
    task = Task.objects.get(id=id)
    return render(request, "detail.html", {"task": task})



def create_checklist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)

    card_id = data.get("card_id")
    title = data.get("title", "Việc cần làm")

    if not card_id:
        return JsonResponse({"error": "Missing card_id"}, status=400)

    card = Card.objects.get(id=card_id)

    checklist = Checklist.objects.create(
        card=card,
        title=title
    )

    return JsonResponse({
        "status": "ok",
        "checklist_id": checklist.id,
        "title": checklist.title
    })

@csrf_exempt
@login_required
def add_checklist_item(request):
    if request.method == "POST":
        data = json.loads(request.body)
        checklist_id = data.get("checklist_id")
        title = data.get("title")

        checklist = get_object_or_404(Checklist, id=checklist_id)

        item = ChecklistItem.objects.create(
            checklist=checklist,
            title=title,
            position=checklist.items.count()
        )

        return JsonResponse({
            "id": item.id,
            "title": item.title,
            "is_done": item.is_done
        })


@csrf_exempt
@login_required
def toggle_checklist_item(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    item_id = data.get("item_id")

    item = get_object_or_404(ChecklistItem, id=item_id)
    item.is_done = not item.is_done
    item.save()

    return JsonResponse({
        "is_done": item.is_done
    })


@csrf_exempt
@login_required
def delete_checklist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        checklist_id = data.get("checklist_id")

        if not checklist_id:
            return JsonResponse({"error": "Missing checklist_id"}, status=400)

        # Kiểm tra checklist có tồn tại không
        checklist = get_object_or_404(Checklist, id=checklist_id)

        # Xóa
        checklist.delete()

        return JsonResponse({"status": "ok", "message": "Deleted successfully"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

'''def findBoard(request):
    boards  = Board.objects.all()
    search_input =""
    if request.method=="POST":
        search_input =request.POST["search"]
        if search_input:
            boards = boards.filter(name__icontains=search_input)
            if boards.count() == 1:
                board_id = boards.first().id
                return redirect('board_detail', pk=board_id)
    return render(request,"BangCVcuaToi.html")'''
def findBoard2(request):
    # Mặc định lấy tất cả
     boards = Board.objects.all()
     search_input = ""

     if request.method == "POST":
        search_input = request.POST.get("search", "")
        
        if search_input:
            # Dùng filter để không bị lỗi nếu có nhiều kết quả
            results = Board.objects.filter(name__icontains=search_input)
            
            # --- LOGIC CHUYỂN TRANG ---
            
            # Trường hợp 1: Tìm thấy đúng 1 bảng duy nhất -> Chuyển ngay sang trang chi tiết
            if results.count() == 1:
                board_id = results.first().id
                return redirect('board_detail', pk=board_id) # Chuyển trang là ở đây
            
            # Trường hợp 2: Tìm thấy nhiều bảng hoặc không thấy -> Hiện danh sách lọc
            boards = results

    # Render lại trang hiện tại với danh sách kết quả
     return render(request, "BangCVcuaToi.html", {
        "boards": boards,
        "search_term": search_input
     })
from django.shortcuts import render, redirect
from .models import Board

def findBoard(request):
    boards = Board.objects.all()
    search_input = ""
    if request.method == "POST":
        search_input = request.POST.get("search", "")
        
        if search_input:
            results = Board.objects.filter(name__icontains=search_input)
            if results.count() == 1:
                board = results.first()
                return redirect('board_detail', board_id=board.id) 
            boards = results

    return render(request, "TrangChu.html")
def search_suggest(request):
    query = request.GET.get('term', '')
    results = []
    
    if query:
        # Lọc bảng theo tên (giới hạn 5-10 kết quả để load cho nhanh)
        boards = Board.objects.filter(name__icontains=query)[:10]
        
        # Chuyển đổi dữ liệu thành danh sách Dictionary
        for board in boards:
            results.append({
                'id': board.id,
                'name': board.name,
                # Có thể thêm ảnh bìa hoặc thông tin khác nếu muốn
            })
    
    # Trả về JSON (safe=False cho phép trả về list)
    return JsonResponse(results, safe=False)

