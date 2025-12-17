import random

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from accounts.models import EmailOTP, User
from todo import settings
from django.contrib import messages


# def sign_in(request):
#     return render(request, 'accounts/login.html')

def sign_up(request):
    return render(request, 'accounts/register.html')

def reset_pass(request):
    return render(request, 'accounts/resetPassword.html')

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

                base_url = reverse('finish_signup')
                redirect_url = f"{base_url}?email={email}"

                return redirect(redirect_url)
                # ------------------------------

            else:
                error = "Mã OTP không đúng hoặc đã hết hạn."
        except EmailOTP.DoesNotExist:
            error = "Email này chưa yêu cầu mã OTP."

    return render(request, 'accounts/verify.html', {'email': email, 'error': error})

def finish_signup(request):
    return render(request, 'accounts/finishSettingUpAccount.html')

def create_name_pass(request):
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ Form
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

            # 4. TỰ ĐỘNG ĐĂNG NHẬP LUÔN
            login(request, new_user)

            # 5. Chuyển hướng về trang chủ
            return redirect('home_page')

        except Exception as e:
            print("Lỗi tạo user:", e)
            return render(request, 'accounts/finishSettingUpAccount.html', {'error': 'Có lỗi hệ thống xảy ra.'})

    return render(request, 'accounts/finishSettingUpAccount.html')
 
def verify_acc(request):
     return render(request, 'accounts/finishResetPassword.html')

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
                if not remember:
                    # Nếu không tick, session sẽ hết hạn khi đóng trình duyệt
                    request.session.set_expiry(0)

                    # Chuyển hướng về trang chủ
                return redirect('home_page')
            else:
                # Đăng nhập thất bại
                error_message = "Tài khoản hoặc mật khẩu không chính xác."

    return render(request, 'accounts/login.html', {'error': error_message})

def logout_view(request):
    logout(request)
    return redirect('sign_in')
