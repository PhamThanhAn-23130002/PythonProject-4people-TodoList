from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required

# Import models
from .models import Notification
from boards.models import Card


@login_required
def get_notifications_api(request):
    user = request.user

    # LOGIC KIỂM TRA DEADLINE TỰ ĐỘNG (LAZY CHECK)

    now = timezone.now()
    one_day_later = now + timedelta(days=1)

    # Tìm các công việc (Card) thỏa mãn 3 điều kiện:
    # + User hiện tại nằm trong danh sách thành viên
    # + Deadline còn dưới 1 ngày
    # + Công việc chưa hoàn thành
    upcoming_cards = Card.objects.filter(
        members=user,
        deadline__range=(now, one_day_later),
        is_completed=False
    ).distinct()

    # Duyệt qua từng công việc tìm được để tạo thông báo
    for card in upcoming_cards:
        # Kiểm tra xem đã gửi thông báo cho công việc này chưa
        already_notified = Notification.objects.filter(
            user=user,
            task=card,
            type='deadline'
        ).exists()

        if not already_notified:
            msg_content = (
                f"Công việc '{card.title}' "
                f"tại danh sách '{card.list.title}' "
                f"sắp hết hạn (Deadline: {card.deadline.strftime('%H:%M %d/%m')})"
            )
            # Tạo thông báo mới
            Notification.objects.create(
                user=user,
                task=card,
                project=card.list.board,
                type='deadline',
                message=msg_content,
                is_read=False
            )

    # LẤY DỮ LIỆU ĐỂ TRẢ VỀ CHO GIAO DIỆN

    # Lấy danh sách thông báo của user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    data = []
    for noti in notifications:
        data.append({
            'id': noti.id,
            'message': noti.message,
            'created_at': noti.created_at.strftime("%d/%m %H:%M"),  # Format ngày giờ
            'is_read': noti.is_read,
            'type': noti.get_type_display(),  # Lấy tên hiển thị
            'task_id': noti.task.id if noti.task else None  # Gửi kèm ID công việc
        })

    # Đếm số lượng thông báo chưa đọc
    unread_count = notifications.filter(is_read=False).count()

    return JsonResponse({
        'status': 'success',
        'notifications': data,
        'unread_count': unread_count
    })


@login_required
def mark_read_api(request, noti_id):
    if request.method == 'GET':
        try:
            noti = Notification.objects.get(id=noti_id, user=request.user)
            noti.is_read = True
            noti.save()
            return JsonResponse({'status': 'success', 'message': 'Đã đánh dấu đã đọc'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông báo'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})