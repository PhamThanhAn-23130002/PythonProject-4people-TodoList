from django.shortcuts import render, redirect, get_object_or_404
from .models import Tag
from boards.models import Card

def task_list(request):
    return render(request, 'boards/TrangChu.html')


def add_tag_to_card(request, card_id):
    if request.method == "POST":
        card = get_object_or_404(Card, id=card_id)
        
        # Lấy dữ liệu từ form
        tag_name = request.POST.get('name')
        tag_color = request.POST.get('color') # Ví dụ: #ff0000

        if tag_name:
            # 1. Tạo Tag mới
            # (Hoặc dùng get_or_create nếu muốn tái sử dụng tag cùng tên)
            tag = Tag.objects.create(name=tag_name, color=tag_color)
            
            # 2. Gắn Tag vào Card (Vì quan hệ ManyToMany)
            tag.cards.add(card)
        
        # 3. Quay lại trang bảng (Cần lấy ID của board từ card)
        return redirect('board_detail', board_id=card.list.board.id)
    
    # Nếu không phải POST thì quay về luôn
    return redirect('home')

def remove_tag_from_card(request, card_id, tag_id):
    card = get_object_or_404(Card, id=card_id)
    tag = get_object_or_404(Tag, id=tag_id)
    
    # Gỡ tag khỏi card
    card.tags.remove(tag)
    
    # Quay lại trang chi tiết bảng
    return redirect('board_detail', board_id=card.list.board.id)


