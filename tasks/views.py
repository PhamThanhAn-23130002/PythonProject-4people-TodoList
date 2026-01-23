from datetime import timezone
import json
from time import localtime
from django.shortcuts import render, redirect, get_object_or_404
from .models import Tag
from boards.models import Card
from .models import Card, Tag
from django.http import JsonResponse
from tasks.models import Comment 
from boards.models import Card
from django.views.decorators.csrf import csrf_exempt

def task_list(request):
    return render(request, 'boards/TrangChu.html')


def add_tag_to_card(request, card_id):
    if request.method == "POST":
        card = get_object_or_404(Card, id=card_id)
        
        tag_name = request.POST.get('name')
        tag_color = request.POST.get('color')

        if tag_name:
            tag = Tag.objects.create(name=tag_name, color=tag_color)
            
            tag.cards.add(card)
        
        return redirect('board_detail', board_id=card.list.board.id)
    return redirect('home')

def remove_tag_from_card(request, card_id, tag_id):
    if request.method == "POST":
        try:
            card = get_object_or_404(Card, id=card_id)
            tag = get_object_or_404(Tag, id=tag_id)
            
            card.tags.remove(tag)
            return JsonResponse({'status': 'success', 'message': 'Đã gỡ nhãn'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def add_comment_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            card_id = data.get('card_id')
            content = data.get('content')
            print(f"👉 DEBUG SERVER: Đang thêm comment vào Card {card_id}: {content}")

            if not content:
                return JsonResponse({'status': 'error', 'message': 'Nội dung trống'})
            card = Card.objects.get(id=int(card_id))
            

            new_cmt = Comment.objects.create(
                card=card,
                author=request.user,
                content=content
            )
            try:

                local_time = timezone.localtime(new_cmt.created_at)
                time_str = local_time.strftime("%H:%M %d/%m")
            except Exception as e:
                print(f"⚠️ Lỗi format ngày: {e}")
                time_str = str(new_cmt.created_at)
            return JsonResponse({
                'status': 'success',
                'username': request.user.username,
                'avatar_char': request.user.username[0].upper() if request.user.username else "?",
                'content': new_cmt.content,
                'created_at': time_str 
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def get_comments_api(request, card_id):
    try:
        card = get_object_or_404(Card, id=card_id)
        comments = card.comments.all().order_by('-created_at')
        
        data = []
        for c in comments:
            try:
                time_str = timezone.localtime(c.created_at).strftime("%H:%M %d/%m")
            except:
                time_str = str(c.created_at)

            data.append({
                'username': c.author.username,
                'avatar': c.author.username[0].upper() if c.author.username else "?",
                'content': c.content,
                'created_at': time_str 
            })
            
        return JsonResponse({'status': 'success', 'comments': data})
    except Exception as e:
        print(f"Lỗi lấy comment: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})


