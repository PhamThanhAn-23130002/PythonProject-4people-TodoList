# boards/utils.py
from boards.models import Card

# Đếm số lượng task (card) mà một người dùng đang được phân công trong board hiện tại và chưa hoàn thành.
def count_tasks_in_board(user, board):
    return Card.objects.filter(
        members=user,
        list__board=board,
        is_completed=False
    ).count()

# Đếm số task mà người dùng đang đảm nhận ở các board (dự án) khác, không bao gồm board hiện tại.
def count_tasks_in_other_boards(user, board):
    return Card.objects.filter(
        members=user,
        is_completed=False
    ).exclude(
        list__board=board
    ).count()


# Tính điểm ưu tiên công việc (priority score) của người dùng dựa trên số lượng task đang đảm nhận.
# diem ban đầu là 100, mỗi task trong board hiện tại làm giảm 5 điểm, mỗi task ở board khác làm giảm 10 điểm
# ccong thức tính: Priority Score = 100 - (Số task trong board hiện tại × 5) - (Số task ở board khác × 10)
def calculate_priority_score(user, board):
    BASE_SCORE = 100
    CURRENT_BOARD_PENALTY = 5
    OTHER_BOARD_PENALTY = 10

    tasks_current = count_tasks_in_board(user, board)
    tasks_other = count_tasks_in_other_boards(user, board)

    score = BASE_SCORE - (tasks_current * CURRENT_BOARD_PENALTY) - (tasks_other * OTHER_BOARD_PENALTY)
    return max(score, 0)
