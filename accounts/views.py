import random

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.urls import reverse
from accounts.models import EmailOTP
from todo import settings


def sign_in(request):
    return render(request, 'accounts/login.html')

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
     return render(request, 'boards/TrangChu.html')
 
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
