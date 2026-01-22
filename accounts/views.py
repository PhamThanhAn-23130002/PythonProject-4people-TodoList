import json
import random
from django.core import signing
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from accounts.models import EmailOTP, User
from todo import settings
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile, Skill # Import đúng model của bạn
import uuid
from django.db.models import Count

# def sign_in(request):
#     return render(request, 'accounts/login.html')

def sign_up(request):
    return render(request, 'accounts/register.html')

def reset_pass(request):
    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email')

        # Kiểm tra email có tồn tại trong hệ thống không
        if not User.objects.filter(email=email).exists():
            error_message = "Email này không tồn tại trong hệ thống."
        else:
            # Tạo mã OTP ngẫu nhiên 6 số
            otp_code = str(random.randint(100000, 999999))

            # Lưu hoặc cập nhật OTP vào database
            EmailOTP.objects.update_or_create(email=email, defaults={'otp': otp_code})

            # Gửi email
            subject = 'Mã xác thực khôi phục mật khẩu TodoList'
            message = f'Mã OTP của bạn là: {otp_code}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, email_from, recipient_list)

            # Lưu email vào session để dùng cho các bước sau
            request.session['reset_email'] = email

            # Chuyển sang trang xác thực
            return redirect('verify_acc')

    return render(request, 'accounts/resetPassword.html', {'error_message': error_message})

# API nhận yêu cầu gửi OTP từ Javascript (AJAX)
def send_otp_api(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email không được để trống'})

        # Tạo OTP và lưu DB
        otp_code = str(random.randint(100000, 999999))
        EmailOTP.objects.update_or_create(email=email, defaults={'otp': otp_code})

        # Gửi Email
        try:
            send_mail(
                'Mã xác thực TodoList',
                f'Mã OTP của bạn là: {otp_code}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def verify_code(request):
    email = request.GET.get('email', '')
    error = None

    if request.method == 'POST':
        email = request.POST.get('email')
        otp_input = request.POST.get('otp_full')

        try:
            otp_record = EmailOTP.objects.get(email=email)
            if otp_record.otp == otp_input and otp_record.is_valid():
                otp_record.delete()

                # base_url = reverse('finish_signup')
                # redirect_url = f"{base_url}?email={email}"
                request.session['email'] = email
                request.session.modified = True

                return redirect('create_name_pass')
                # ------------------------------

            else:
                error = "Mã OTP không đúng hoặc đã hết hạn."
        except EmailOTP.DoesNotExist:
            error = "Email này chưa yêu cầu mã OTP."

    return render(request, 'accounts/verify.html', {'email': email, 'error': error})

def finish_signup(request):
    return render(request, 'accounts/finishSettingUpAccount.html')

def create_name_pass(request):
    if request.method == 'GET':
        email = request.session.get('email')
        if not email:
            return redirect('sign_up')
        return render(request, 'accounts/finishSettingUpAccount.html', {'email': email})

    if request.method == 'POST':
        # 1. Lấy dữ liệu từ Form
        # email = request.POST.get('email')
        email = request.session.get('email')
        if not email:
            email = request.POST.get('email')
        fullname = request.POST.get('fullname')
        password = request.POST.get('password')

        # Kiểm tra sơ bộ
        if not email or not password:
            return render(request, 'accounts/finishSettingUpAccount.html', {'error': 'Thiếu thông tin!'})

        # 2. Kiểm tra Email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return render(request, 'accounts/finishSettingUpAccount.html', {
                'error': 'Email này đã được đăng ký.',
                'email': email
            })

        try:
            # 3. TẠO USER MỚI
            # create_user sẽ tự động MÃ HÓA (Hash) password cho bạn.
            # Vì AbstractUser bắt buộc có username, ta lấy luôn email làm username
            new_user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            # Lưu Fullname vào trường first_name có sẵn của Django
            new_user.first_name = fullname
            new_user.save()

            if hasattr(settings, 'AUTHENTICATION_BACKENDS') and settings.AUTHENTICATION_BACKENDS:
                new_user.backend = settings.AUTHENTICATION_BACKENDS[0]
            else:
                new_user.backend = 'django.contrib.auth.backends.ModelBackend'

            # 4. TỰ ĐỘNG ĐĂNG NHẬP LUÔN
            login(request, new_user)

            if 'email' in request.session:
                del request.session['email']

            # 5. Chuyển hướng về trang chủ
            return redirect('home_page')

        except Exception as e:
            print("Lỗi tạo user:", e)
            return render(request, 'accounts/finishSettingUpAccount.html', {'error': 'Có lỗi hệ thống xảy ra.'})

    return render(request, 'accounts/finishSettingUpAccount.html')
 
def verify_acc(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('reset_pass')

    error_message = None

    if request.method == 'POST':
        otp_input = request.POST.get('otp_full')  # Lấy OTP từ input hidden

        try:
            otp_record = EmailOTP.objects.get(email=email)
            if otp_record.otp == otp_input:
                otp_record.delete()
                request.session['otp_verified'] = True
                return redirect('change_pass')
            else:
                error_message = "Mã OTP không chính xác."
        except EmailOTP.DoesNotExist:
            error_message = "Yêu cầu hết hạn, vui lòng thử lại."

    return render(request, 'accounts/finishResetPassword.html', {'email': email, 'error_message': error_message})

def SitePerSonal(request):
    return render(request,'accounts/SitePersonal.html')

def setting(request):
    return render(request,'accounts/setting.html')

def action(request):
    return render(request,'accounts/hoatdong.html')

def card(request):
    return render(request,'accounts/card.html')

def boardspersonal(request):
    return render(request,'accounts/boards.html')

def members(request):
    return render(request,'accounts/members.html')


def sign_in(request):
    # Nếu người dùng đã đăng nhập rồi thì về trang chủ luôn, không cần hiện form login nữa
    if request.user.is_authenticated:
        return redirect('home_page')

    initial_email = request.GET.get('email', '')
    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kiểm tra xem có nhập đủ thông tin không
        if not email or not password:
            error_message = "Vui lòng nhập đầy đủ Email và Mật khẩu."
        else:
            # --- QUAN TRỌNG ---
            # Hàm authenticate kiểm tra user trong database.
            # Vì lúc đăng ký ta lưu username = email, nên ở đây tham số username ta truyền vào email.
            user = authenticate(request, username=email, password=password)

            if user is not None:
                # Đăng nhập thành công
                login(request, user)

                # Kiểm tra xem có tick vào ô "Nhớ mật khẩu" không
                remember = request.POST.get('remember_me')
                is_remembered = True if remember else False
                if not remember:
                    # Nếu không tick, session sẽ hết hạn khi đóng trình duyệt
                    request.session.set_expiry(0)

                response = redirect('home_page')  # Chuyển hướng về trang chủ
                set_login_history_cookie(request, response, user, is_remembered)
                return response
            else:
                # Đăng nhập thất bại
                error_message = "Tài khoản hoặc mật khẩu không chính xác."
    context = {
        'error': error_message,
        'initial_email': initial_email
    }
    return render(request, 'accounts/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('sign_in')

def switch_account(request):
    # Nếu chưa đăng nhập -> về login
    if not request.user.is_authenticated:
        return redirect('sign_in')

    # Lấy lịch sử từ Cookie
    history_str = request.COOKIES.get('login_history', '[]')
    try:
        history_list = json.loads(history_str)
    except json.JSONDecodeError:
        history_list = []

    # Loại bỏ tài khoản hiện tại ra khỏi danh sách lịch sử
    previous_accounts = [
        acc for acc in history_list
        if acc['email'] != request.user.email
    ]

    context = {
        'previous_accounts': previous_accounts,
    }
    return render(request, 'accounts/switchAccount.html', context)


# --- Lưu lịch sử đăng nhập ---
# Hàm này được gọi sau khi người dùng đăng nhập
def set_login_history_cookie(request, response, user, is_remembered=False):
    # 1. Đọc lịch sử cũ
    history_str = request.COOKIES.get('login_history', '[]')
    try:
        history_list = json.loads(history_str)
    except Exception:
        history_list = []

    # 2. Tạo Token bí mật nếu người dùng chọn "Nhớ mật khẩu"
    # Token này sẽ hoạt động như một vé thông hành để vào thẳng trang chủ
    secret_token = None
    if is_remembered:
        # Tạo chữ ký chứa ID người dùng (an toàn, không thể giả mạo)
        secret_token = signing.dumps({'user_id': user.id})

    # 3. Tạo object thông tin user
    user_info = {
        'username': user.username,
        'email': user.email,
        'avatar_char': user.username[0].upper() if user.username else "?",
        'token': secret_token  # <--- Lưu token vào đây
    }

    # 4. Xóa user này nếu đã có trong lịch sử (để update cái mới nhất lên đầu)
    history_list = [acc for acc in history_list if acc['email'] != user.email]

    # 5. Thêm vào đầu danh sách
    history_list.insert(0, user_info)
    history_list = history_list[:5]  # Giới hạn 5 tài khoản

    # 6. Lưu cookie (lưu ý: max_age 1 năm)
    response.set_cookie('login_history', json.dumps(history_list), max_age=365 * 24 * 60 * 60)

    return response


def switch_to_other_account(request):
    """
    Hàm này xử lý khi người dùng bấm vào một tài khoản cũ trong lịch sử:
    1. Lấy email cần chuyển tới.
    2. Đăng xuất tài khoản hiện tại.
    3. Chuyển hướng về trang Login và điền sẵn email kia.
    """
    # Lấy email từ URL (do bấm link gửi lên)
    target_email = request.GET.get('email', '')

    # Đăng xuất tài khoản hiện tại (Quan trọng!)
    logout(request)

    # Tìm kiếm trong Cookie xem tài khoản này có Token "Nhớ mật khẩu" không
    history_str = request.COOKIES.get('login_history', '[]')
    found_token = None

    try:
        history_list = json.loads(history_str)
        # Tìm user có email khớp
        for acc in history_list:
            if acc.get('email') == target_email:
                found_token = acc.get('token')
                break
    except Exception:
        pass

        # Nếu tìm thấy Token, thử giải mã và đăng nhập luôn
    if found_token:
        try:
            # Giải mã token (max_age=2 tuần - ví dụ token chỉ sống 2 tuần)
            data = signing.loads(found_token, max_age=14 * 24 * 60 * 60)
            user_id = data.get('user_id')

            # Tìm user trong database
            User = get_user_model()
            user = User.objects.get(pk=user_id)

            # --- QUAN TRỌNG: Đăng nhập không cần mật khẩu ---
            # Cần chỉ định backend vì ta không dùng authenticate()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Chuyển thẳng về trang chủ
            return redirect('home_page')

        except (signing.BadSignature, User.DoesNotExist):
            # Nếu token sai, hết hạn, hoặc user bị xóa -> Bỏ qua, xuống dưới login thường
            pass

    # Tạo đường dẫn về trang Login
    login_url = reverse('sign_in')

    # Nếu có email thì nối thêm tham số ?email=... vào đuôi
    if target_email:
        return redirect(f'{login_url}?email={target_email}')

    # Nếu không có email thì về trang login bình thường
    return redirect('accounts/sign_in')

def change_pass(request):
    email = request.session.get('reset_email')
    is_verified = request.session.get('otp_verified')

    if not email or not is_verified:
        return redirect('reset_pass')

    message = None
    is_success = False

    if request.method == 'POST':
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            message = "Mật khẩu nhập lại không đúng."
        else:
            # Đổi mật khẩu
            user = User.objects.get(email=email)
            user.set_password(pass1)
            user.save()

            message = "Đổi mật khẩu hoàn tất."
            is_success = True

            # Xóa session để hoàn tất quy trình
            del request.session['reset_email']
            del request.session['otp_verified']

    return render(request, 'accounts/changePasswordAfterVerify.html', {
        'message': message,
        'is_success': is_success
    })
