# boards/utils.py
from boards.models import Card

def user_has_task_in_other_boards(user, current_board):
    """
    Kiểm tra user có card chưa hoàn thành ở board khác hay không
    """
    return Card.objects.filter(
        members=user,
        is_completed=False
    ).exclude(
        list__board=current_board
    ).exists()
