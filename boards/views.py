from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model
from django.contrib import messages
from django.http import HttpResponse, request, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import json

# Import Models
from .models import Board, BoardMember, List, Card, Checklist, ChecklistItem

User = get_user_model()


# ============================================================================
# PHẦN 1: CÁC VIEW RENDER TEMPLATE (TRANG TĨNH HOẶC ÍT LOGIC)
# ============================================================================

# Render trang tạo bảng (Giao diện đơn giản)
def create_board(request):
    return render(request, "boards/BangCVcuaToi.html")


# # Render trang chi tiết thẻ (Template gốc)
# def card_detail(request):
#     return render(request, "boards/CardDetail.html")

# Render trang chủ (Phiên bản template 1)
def home_page_template_1(request):
    return render(request, "boards/TrangChu.html")


# Render trang chủ (Phiên bản template 2)
def home_page2(request):
    return render(request, "boards/TrangChu2.html")


# Render trang chủ dạng Bảng
def home_page_Table(request):
    return render(request, "boards/TrangChu-Bang.html")


# Render trang giới thiệu bản thân
def about_me(request):
    return render(request, "accounts/SitePersonal.html")


# ============================================================================
# PHẦN 2: LOGIC TRANG CHỦ & QUẢN LÝ BOARD (BẢNG)
# ============================================================================

# Xử lý tắt hướng dẫn (Intro)
def dismiss_intro(request):
    request.session['intro_dismissed'] = True
    return redirect('home_page')


# 1. Trang chủ chính: Hiển thị danh sách các bảng của user
@login_required(login_url='/login/')
def home_page(request):
    # Lấy các bảng user làm chủ HOẶC user là thành viên
    boards = Board.objects.filter(
        Q(owner=request.user) | Q(boardmember__user=request.user)
    ).distinct().order_by('-created_at')

    show_intro = not request.session.get('intro_dismissed', False)

    context = {
        'boards': boards,
        'show_intro': show_intro,
    }
    return render(request, "boards/TrangChu.html", context)


# 2. Xử lý tạo Board mới (Form Submit)
@login_required(login_url='/login/')
def create_board_logic(request):
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
            # Tự động thêm người tạo làm admin
            BoardMember.objects.create(
                project=new_board,
                user=request.user,
                role='admin'
            )
            return redirect('home_page')

    return redirect('home_page')


# 3. Trang chi tiết Bảng (Hiển thị Lists và Cards)
def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    members = BoardMember.objects.filter(project=board)

    # Lấy danh sách kèm theo thẻ (tối ưu query bằng prefetch_related)
    lists = List.objects.filter(board=board).prefetch_related("cards").order_by("position")

    context = {
        "board": board,
        "members": members,
        "lists": lists,
        "all_boards": Board.objects.filter(owner=request.user)
    }
    return render(request, "boards/BangCVcuaToi.html", context)


# 4. Xử lý thêm thành viên vào bảng qua Email
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


# 5. Xử lý xóa Bảng
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


# 6. Xử lý tham gia bảng qua Link chia sẻ
def join_via_link(request, token):
    board = get_object_or_404(Board, share_token=token)

    if not request.user.is_authenticated:
        return redirect('/login/')

    if not BoardMember.objects.filter(project=board, user=request.user).exists():
        BoardMember.objects.create(project=board, user=request.user, role='member')
        messages.success(request, f"Bạn đã tham gia vào bảng {board.name} thành công!")
    else:
        messages.info(request, "Bạn đã là thành viên của bảng này rồi.")

    return redirect('board_detail', board_id=board.id)


# 7. (LƯU Ý) Hàm lưu toàn bộ bảng - CÓ THỂ GÂY MẤT DỮ LIỆU CŨ
# Khuyến khích dùng create_list_api và create_card_api thay thế
def save_board_db(request, board_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    lists_data = data.get("lists", [])
    board = Board.objects.get(id=board_id)

    # XÓA toàn bộ list cũ và tạo lại (Cẩn thận khi dùng)
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


# ============================================================================
# PHẦN 3: LOGIC CHI TIẾT THẺ & CHECKLIST
# ============================================================================

# API: Tạo Checklist mới
def create_checklist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    card_id = data.get("card_id")
    title = data.get("title", "Việc cần làm")

    if not card_id:
        return JsonResponse({"error": "Missing card_id"}, status=400)

    card = Card.objects.get(id=card_id)
    checklist = Checklist.objects.create(card=card, title=title)

    return JsonResponse({
        "status": "ok",
        "checklist_id": checklist.id,
        "title": checklist.title
    })


# API: Thêm mục con vào Checklist
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


# API: Đánh dấu hoàn thành mục Checklist
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

    return JsonResponse({"is_done": item.is_done})


# API: Xóa Checklist
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

        checklist = get_object_or_404(Checklist, id=checklist_id)
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
@login_required
def get_card_checklists(request, card_id):
    card = get_object_or_404(Card, id=card_id)

    checklists = []
    for cl in card.checklists.prefetch_related("items"):
        checklists.append({
            "id": cl.id,
            "title": cl.title,
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "is_done": item.is_done
                }
                for item in cl.items.all()
            ]
        })

    return JsonResponse(checklists, safe=False)


@csrf_exempt
@login_required
def delete_checklist_item(request):
    data = json.loads(request.body)
    item_id = data.get("item_id")
    item = get_object_or_404(ChecklistItem, id=item_id)
    item.delete()
    return JsonResponse({"status": "ok"})


# ============================================================================
# PHẦN 4: CÁC HÀM XỬ LÝ CARD CŨ/PHỤ (Legacy)
# ============================================================================

# Tạo deadline (Hàm cũ, có thể không còn dùng)
def createdealine(request):
    if request.method == "POST":
        d1 = request.POST.get("title")
        d2 = request.POST.get("description")
        d3 = request.POST.get("priority")
        d4 = request.POST.get("process")
        d5 = request.POST.get("complexity")
        d6 = request.POST.get("inputdate")
        d7 = request.POST.get("inputtime")
        dt = datetime.strptime(f"{d6} {d7}", "%Y-%m-%d %H:%M")
        Card.objects.create(
            title=d1, description=d2, priority=d3,
            status=d4, difficulty=d5, deadline=dt
        )
        return redirect("boards/BangCVcuaToi.html")


# Load deadline (Hàm cũ)
def loaddealine(request, id):
    card = Card.objects.get(id=id)  # Đã sửa cú pháp id==id thành id=id
    dealine = card.deadline
    if timezone.is_aware(dealine):
        dealine = timezone.localtime(dealine)
    context = {
        "deadline_date": dealine.date(),
        "deadline_time": dealine.time().strftime("%H:%M"),
    }
    return render(request, "CardDetail.html", context)


# Chi tiết task (Hàm cũ)
def detail_task(request, id):
    task = Card.objects.get(id=id)
    return render(request, "detail.html", {"task": task})


# ============================================================================
# PHẦN 5: API QUẢN LÝ THÀNH VIÊN TRONG THẺ (MEMBER)
# ============================================================================

# API: Gán thành viên (Phiên bản cũ)
def assign_member_to_card(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            username = data.get('username')
            action = data.get('action')

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


# API: Cập nhật thành viên (Phiên bản khác)
@csrf_exempt
def update_card_member(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            username = data.get('username')
            action = data.get('action')

            card = get_object_or_404(Card, id=card_id)
            user = get_object_or_404(User, username=username)

            if action == 'add':
                card.members.add(user)
                message = f"Đã thêm {username} vào thẻ."
            elif action == 'remove':
                card.members.remove(user)
                message = f"Đã xóa {username} khỏi thẻ."

            return JsonResponse({'status': 'ok', 'message': message})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# API: Quản lý thành viên (Phiên bản mới nhất - Nên dùng cái này)
def manage_card_member(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            username = data.get('username')
            action = data.get('action')

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


# ============================================================================
# PHẦN 6: API CẬP NHẬT THUỘC TÍNH THẺ (Tên, Ngày, Xóa...)
# ============================================================================

# API: Cập nhật Deadline
def update_card_deadline(request, card_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            date_str = data.get('date')
            time_str = data.get('time')

            card = get_object_or_404(Card, id=card_id)

            if date_str:
                if not time_str: time_str = "09:00"
                full_datetime_str = f"{date_str} {time_str}"
                card.deadline = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M")
                card.save()
                return JsonResponse({'status': 'success', 'message': 'Đã lưu ngày hết hạn'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# API: Cập nhật Tên thẻ (Rename)
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


# API: Xóa Thẻ (An toàn)
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


# ============================================================================
# PHẦN 7: API TẠO/XÓA DANH SÁCH & THẺ (AN TOÀN - KHÔNG MẤT DỮ LIỆU)
# ============================================================================

# 1. API Tạo Danh Sách Mới (An toàn)
@csrf_exempt
def create_list_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            board_id = data.get('board_id')
            title = data.get('title')

            if not board_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu board_id'})

            board = get_object_or_404(Board, id=board_id)
            position = List.objects.filter(board=board).count()

            new_list = List.objects.create(board=board, title=title, position=position)

            return JsonResponse({'status': 'success', 'id': new_list.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 2. API Tạo Thẻ Mới (An toàn)
@csrf_exempt
def create_card_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            list_id = data.get('list_id')
            title = data.get('title')

            if not list_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu list_id'})

            parent_list = get_object_or_404(List, id=list_id)
            position = Card.objects.filter(list=parent_list).count()

            new_card = Card.objects.create(list=parent_list, title=title, position=position)

            return JsonResponse({'status': 'success', 'id': new_card.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# 3. API Xóa Danh Sách (An toàn)
@csrf_exempt
def delete_list_api(request, list_id):
    if request.method == "POST":
        try:
            target_list = List.objects.get(id=list_id)
            target_list.delete()
            return JsonResponse({'status': 'success'})
        except List.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy danh sách'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'})


# Xử lý chuyện lưu thông tin mô tả của một thẻ xuống db.

def update_card_description(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            description = data.get('description')

            card = get_object_or_404(Card, id=card_id)

            # Cập nhật mô tả (cho phép rỗng)
            card.description = description
            card.save()

            return JsonResponse({'status': 'success', 'message': 'Đã lưu mô tả'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# Trạng thái hoàn thành của thẻ

# boards/views.py

@csrf_exempt
def toggle_card_completed_api(request, card_id):
    if request.method == "POST":
        try:
            card = get_object_or_404(Card, id=card_id)
            # Đảo ngược trạng thái (True -> False, False -> True)
            # Lưu ý: Bạn cần chắc chắn trong models.py, model Card đã có trường is_completed
            # Nếu chưa có, bạn cần thêm: is_completed = models.BooleanField(default=False) và makemigrations

            # Nếu chưa có trường is_completed trong model, hãy tạm dùng 1 trường khác hoặc thêm vào model nhé.
            # Giả sử bạn đã thêm trường is_completed vào Model Card:
            card.is_completed = not card.is_completed
            card.save()

            return JsonResponse({'status': 'success', 'is_completed': card.is_completed})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# Rename tên cho list

@csrf_exempt
def update_list_title(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            list_id = data.get('list_id')
            new_title = data.get('title')

            if not list_id or not new_title:
                return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'})

            # Tìm và cập nhật
            list_obj = get_object_or_404(List, id=list_id)
            list_obj.title = new_title
            list_obj.save()

            return JsonResponse({'status': 'success', 'message': 'Đã đổi tên danh sách'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# Tính năng drag and drop

@csrf_exempt
def move_card_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            new_list_id = data.get('new_list_id')
            new_position = data.get('new_position')  # Vị trí mới (0, 1, 2...)

            # 1. Lấy thẻ và list mới
            card = get_object_or_404(Card, id=card_id)
            target_list = get_object_or_404(List, id=new_list_id)

            # 2. Cập nhật thông tin
            card.list = target_list
            card.position = new_position
            card.save()

            # (Nâng cao: Nếu muốn chuẩn xác 100%, bạn có thể cập nhật lại position 
            # của các thẻ khác trong list đó, nhưng tạm thời cập nhật mình thẻ này là đủ dùng)

            return JsonResponse({'status': 'success', 'message': 'Đã di chuyển thẻ'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
