from django.shortcuts import render
from django.http import HttpResponse

def sign_in(request):
    return render(request, 'accounts/login.html')

def sign_up(request):
    return render(request, 'accounts/register.html')

def reset_pass(request):
    return render(request, 'accounts/resetPassword.html')

def verify_code(request):
    return render(request,'accounts/verify.html')

def finish_signup(request):
    return render(request, 'accounts/finishSettingUpAccount.html')

def create_name_pass(request):
     return render(request, 'boards/TrangChu.html')
 
def verify_acc(request):
     return render(request, 'accounts/finishResetPassword.html')



