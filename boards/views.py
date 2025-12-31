from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model
from .models import Board, BoardMember, User
from django.contrib import messages # Để thông báo lỗi/thành công
from django.http import HttpResponse, request, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from boards.models import Card
import json
from django.db.models import Q #phép tuyển
from .models import Board, List, Card,Checklist, ChecklistItem
from datetime import datetime
from django.utils import timezone
from .models import Card, BoardMember # Import model của bạn

User = get_user_model()
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
    Card.objects.create(
        title = d1,
        description = d2,
        priority = d3, 
        status = d4,
        difficulty =d5,
        deadline = dt)
    return redirect("boards/BangCVcuaToi.html")
def loaddealine(request,id):
    list=Card.objects.get(id==id)
    dealine = list.deadline
    if timezone.is_aware(dealine):
        dealine = timezone.localtime(dealine)
    context={
        "deadline_date": dealine.date(),
        "deadline_time": dealine.time().strftime("%H:%M"),
        
    }
    return render(request, "CardDetail.html", context)
def detail_task(request, id):
    task = Card.objects.get(id=id)
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


def assign_member_to_card(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')  # ID của thẻ (chúng ta sẽ sửa HTML để lấy cái này)
            username = data.get('username')
            action = data.get('action')  # 'add' hoặc 'remove'

            card = Card.objects.get(id=card_id)
            user = User.objects.get(username=username)

            if action == 'add':
                card.members.add(user)
            elif action == 'remove':
                card.members.remove(user)

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@csrf_exempt
def update_card_member(request):
    if request.method == 'POST':
        try:
            # 1. Lấy dữ liệu từ Javascript gửi lên
            data = json.loads(request.body)
            card_id = data.get('card_id')
            username = data.get('username')
            action = data.get('action')  # 'add' hoặc 'remove'

            # 2. Tìm thẻ và user tương ứng
            card = get_object_or_404(Card, id=card_id)
            user = get_object_or_404(User, username=username)

            # 3. Thêm hoặc Xóa khỏi quan hệ Many-to-Many
            if action == 'add':
                card.members.add(user)  # Lưu vào bảng boards_card_members
                message = f"Đã thêm {username} vào thẻ."
            elif action == 'remove':
                card.members.remove(user)  # Xóa khỏi bảng boards_card_members
                message = f"Đã xóa {username} khỏi thẻ."

            return JsonResponse({'status': 'ok', 'message': message})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def update_card_deadline(request, card_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            date_str = data.get('date') # Chuỗi: "2025-12-30"
            time_str = data.get('time') # Chuỗi: "15:30"
            
            card = get_object_or_404(Card, id=card_id)
            
            if date_str:
                # Nếu không chọn giờ, mặc định là 00:00 hoặc giờ hiện tại tùy bạn
                # Ở đây mình gộp ngày và giờ để lưu vào DateTimeField
                if not time_str:
                    time_str = "09:00" # Giờ mặc định nếu user quên chọn giờ
                
                # Tạo chuỗi datetime đầy đủ: "2025-12-30 15:30"
                full_datetime_str = f"{date_str} {time_str}"
                
                # Chuyển đổi sang object datetime
                # Lưu ý: Định dạng phải khớp với chuỗi ghép bên trên
                card.deadline = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M")
                card.save()
                
                return JsonResponse({'status': 'success', 'message': 'Đã lưu ngày hết hạn'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def manage_card_member(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            username = data.get('username')
            action = data.get('action') # 'add' hoặc 'remove'

            card = get_object_or_404(Card, id=card_id)
            user = get_object_or_404(User, username=username)

            if action == 'add':
                card.members.add(user)
                message = f"Đã thêm {username} vào thẻ"
            elif action == 'remove':
                card.members.remove(user)
                message = f"Đã xóa {username} khỏi thẻ"
            else:
                return JsonResponse({'status': 'error', 'message': 'Action không hợp lệ'})

            return JsonResponse({'status': 'success', 'message': message})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid method'})



#Cập nhật tên cho từng thẻ
def update_card_title(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            new_title = data.get('title')
            
            card = get_object_or_404(Card, id=card_id)
            
            if new_title:
                card.title = new_title
                card.save()
                return JsonResponse({'status': 'success', 'message': 'Đã cập nhật tiêu đề'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Tiêu đề không được để trống'})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# xóa thẻ

@csrf_exempt
def delete_card_api(request, card_id):
    if request.method == "POST":
        try:
            card = get_object_or_404(Card, id=card_id)
            card.delete()
            return JsonResponse({'status': 'success', 'message': 'Đã xóa thẻ'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 1. API Tạo Danh Sách Mới (An toàn - Không xóa dữ liệu cũ)
@csrf_exempt
def create_list_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            board_id = data.get('board_id')
            title = data.get('title')
            
            # Kiểm tra board_id hợp lệ
            if not board_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu board_id'})

            board = get_object_or_404(Board, id=board_id)
            
            # Lấy vị trí cuối cùng để xếp danh sách mới xuống dưới
            position = List.objects.filter(board=board).count()
            
            new_list = List.objects.create(board=board, title=title, position=position)
            
            return JsonResponse({'status': 'success', 'id': new_list.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# 2. API Tạo Thẻ Mới (An toàn - Không xóa dữ liệu cũ)
@csrf_exempt
def create_card_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            list_id = data.get('list_id')
            title = data.get('title')
            
            # Kiểm tra list_id
            if not list_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu list_id'})

            parent_list = get_object_or_404(List, id=list_id)
            position = Card.objects.filter(list=parent_list).count()
            
            # Chỉ tạo thẻ mới, dữ liệu các thẻ khác giữ nguyên
            new_card = Card.objects.create(list=parent_list, title=title, position=position)
            
            return JsonResponse({'status': 'success', 'id': new_card.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# 3. API Xóa Danh Sách (An toàn)
# boards/views.py (Thêm vào cuối file)

@csrf_exempt
def delete_list_api(request, list_id):
    if request.method == "POST":
        try:
            # Tìm danh sách theo ID và xóa nó
            target_list = List.objects.get(id=list_id)
            target_list.delete()
            return JsonResponse({'status': 'success'})
        except List.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy danh sách'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'})

