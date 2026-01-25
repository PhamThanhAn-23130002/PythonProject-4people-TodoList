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
from accounts.models import UserProfile, Skill
import uuid
from .models import Board, BoardMember, List, Card, Checklist, ChecklistItem
import numpy as np
from sentence_transformers import SentenceTransformer, util #thư viện để so sánh ngữ nghĩa câu
from boards.utils import count_tasks_in_other_boards, count_tasks_in_board
from django.db.models import Count
from boards.utils import calculate_priority_score

# chuyên dùng để so sánh độ tương đồng ngữ nghĩa
print("Đang tải model AI... vui lòng đợi trong giây lát...")
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model AI đã sẵn sàng!")

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


@login_required(login_url='/login/')
def about_me(request):
    user = request.user

    try:
        profile = UserProfile.objects.get(user_id=user)
    except UserProfile.DoesNotExist:
        # Nếu chưa có thì tạo mới ngay lập tức
        new_id = uuid.uuid4().hex[:10]
        profile = UserProfile.objects.create(
            id=new_id,
            user_id=user,
            role='Member',
            experience_level='Junior'
        )

    if request.method == "POST":
        print("--- DEBUG: Đang xử lý lưu profile tại hàm about_me ---")

        # 1. Lấy dữ liệu từ form
        username = request.POST.get('username')
        bio = request.POST.get('bio')
        experience = request.POST.get('experience')
        skills_text = request.POST.get('skills')

        try:
            # 2. Lưu User (Tên đăng nhập/Email)
            if username and username != user.username:
                user.username = username
                user.save()

            # 3. Lưu Profile (Bio, Kinh nghiệm)
            profile.bio = bio
            profile.experience_level = experience
            profile.save()

            # 4. Lưu Kỹ năng (Tách chuỗi -> Lưu vào DB)
            if skills_text is not None: # Chỉ xử lý khi có input gửi lên
                profile.skill.clear() # Xóa skill cũ để cập nhật mới

                # Tách chuỗi "Python, HTML" thành danh sách ['Python', 'HTML']
                skill_list = [s.strip() for s in skills_text.split(',') if s.strip()]

                for s_name in skill_list:
                    # Kiểm tra skill đã tồn tại trong kho chưa
                    skill_obj = Skill.objects.filter(name__iexact=s_name).first()
                    if not skill_obj:
                        # Chưa có thì tạo mới skill trong kho
                        skill_id = uuid.uuid4().hex[:10]
                        skill_obj = Skill.objects.create(id=skill_id, name=s_name)

                    # Gán skill vào profile người dùng
                    profile.skill.add(skill_obj)

            messages.success(request, "Đã lưu thay đổi thành công!")

        except Exception as e:
            print("Lỗi lưu DB:", e)
            messages.error(request, f"Lỗi: {str(e)}")

        # Load lại chính trang này để thấy dữ liệu mới
        return redirect('about_me')

    # Chuyển danh sách skill thành chuỗi để hiện ra form (VD: "Python, HTML")
    current_skills = ", ".join([s.name for s in profile.skill.all()])

    context = {
        'profile': profile,
        'current_skills': current_skills
    }
    return render(request, "accounts/SitePersonal.html", context)


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
                role='Quản trị viên'
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
                BoardMember.objects.create(project=board, user=user_to_add, role='Thành viên')
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


# 7. Hàm lưu toàn bộ bảng 
def save_board_db(request, board_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    lists_data = data.get("lists", [])
    board = Board.objects.get(id=board_id)

    # XÓA toàn bộ list cũ và tạo lại
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

# API: Quản lý thành viên
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
                board = card.list.board

                priority_score = calculate_priority_score(user, board)
                PRIORITY_THRESHOLD = 30 #điểm chốt để không cho người đó tham gia dự án khác nếu nhỏ hơn cái này

                if priority_score < PRIORITY_THRESHOLD:
                    return JsonResponse({
                        'status': 'warning',
                        'message': f'{username} đang quá tải (điểm ưu tiên: {priority_score})',
                        'priority_score': priority_score
                    })

                card.members.add(user)
                message = f"Đã thêm {username} vào thẻ"

            elif action == 'remove':
                card.members.remove(user)
                message = f"Đã xóa {username} khỏi thẻ"

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Action không hợp lệ'
                })

            return JsonResponse({
                'status': 'success',
                'message': message
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid method'
    })

# tính toán và trả về mức độ ưu tiên công việc (priority score) của một người dùng đối với card đang được xem.
def get_user_priority(request):
    card_id = request.GET.get("card_id")
    username = request.GET.get("username")

    if not card_id or not username:
        return JsonResponse(
            {"error": "Missing card_id or username"},
            status=400
        )

    card = get_object_or_404(Card, id=card_id)
    user = get_object_or_404(User, username=username)

    board = card.list.board
    priority_score = calculate_priority_score(user, board)

    return JsonResponse({
        "priority_score": priority_score
    })


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


# API: Xóa Thẻ
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
# PHẦN 7: API TẠO/XÓA DANH SÁCH & THẺ
# ============================================================================

# 1. API Tạo Danh Sách Mới
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


# 3. API Xóa Danh Sách
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


@csrf_exempt
def ai_auto_assign_member(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            card = get_object_or_404(Card, id=card_id)
            current_board = card.list.board
            
            # Quy định việc kỹ năng qđ 70% và bio, kinh nghiệm là 30%
            WEIGHT_SKILL = 0.7 
            WEIGHT_CONTEXT = 0.3
            PENALTY_RATE = 0.05     # Với mỗi task ng đó đang được phân công phạt 5% mỗi task đang làm
            THRESHOLD = 0.15

            #tiêu chí 1: vector hóa 
            task_text = f"{card.title}. {card.description if card.description else ''}"
            task_embedding = semantic_model.encode(task_text, convert_to_tensor=True)

            # Lấy danh sách thành viên
            members = BoardMember.objects.filter(project=current_board)
            candidates = []

            # Vòng lặp tính toán 3 tiêu chí còn lại
            for mem in members:
                try:
                    user = mem.user
                    profile = UserProfile.objects.get(user_id=user)

                    # tiêu chí 1: kỹ năng, kinh nghiệm
                    #tính điểm kỹ năng
                    skills_list = [s.name for s in profile.skill.all()]
                    skills_text = ", ".join(skills_list) if skills_list else "General"
                    skill_emb = semantic_model.encode(skills_text, convert_to_tensor=True)
                    skill_score = util.cos_sim(task_embedding, skill_emb)[0].item()

                    # Tính điểm bio, kinh nghiệm
                    context_text = f"{profile.role} {profile.experience_level} {profile.bio}"
                    context_emb = semantic_model.encode(context_text, convert_to_tensor=True)
                    context_score = util.cos_sim(task_embedding, context_emb)[0].item()

                    # Score(AI)
                    base_score = (skill_score * WEIGHT_SKILL) + (context_score * WEIGHT_CONTEXT)

                    # tiêu chí 2 và 3: số task đang được phân trong dự án và các dự án khác
                    local_load = count_tasks_in_board(user, current_board)
                    global_load = count_tasks_in_other_boards(user, current_board)
                    
                    total_load = (local_load + global_load)*PENALTY_RATE
                    
                    # Công thức: Final = Base * (1 - P(load))
                    final_score = base_score * (1 - total_load)

                    candidates.append({
                        'username': user.username,
                        'user_obj': user,
                        'final_score': final_score,
                        'base_score': base_score,
                        'local': local_load,
                        'global': global_load
                    })

                except UserProfile.DoesNotExist:
                    continue

            # sx chọn ra ng tốt nhất 
            candidates.sort(key=lambda x: x['final_score'], reverse=True)

            if candidates and candidates[0]['final_score'] > THRESHOLD:
                best = candidates[0]
                user_to_add = best['user_obj']

                if not card.members.filter(id=user_to_add.id).exists():
                    card.members.add(user_to_add)
                reason = (
                    f"⭐ Độ phù hợp: {round(best['base_score']*100, 1)}%\n"
                    f"📉 Đang bận: {best['local']} task ở đây "
                    f"+ {best['global']} task dự án khác.\n"
                    f"✅ Điểm quyết định: {round(best['final_score']*100, 1)}%"
                )

                return JsonResponse({'status': 'success', 'username': best['username'], 'reason': reason})
            else:
                return JsonResponse({'status': 'error', 'message': "Không tìm thấy ai phù hợp hoặc mọi người đều đang quá tải."})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def countTask(board_id):
     return((
        User.objects
        .filter(cards__list__board_id=board_id)
        .annotate(total_tasks=Count('cards', distinct=True))
        .values('id', 'total_tasks')
    ))
def countTaskUser(User_id):
    return User.objects.get(User_id).annotate(toal_task=Count('cards',distinct=True)).values('id','toal_tasks')