from django.http.response import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib import messages

from .models import CustomUser
from .forms import RegistrationForm, UserEditForm
from .tokens import account_activation_token

def homeview(request):
    return render(request, 'users/home.html')

@login_required
def dashboard(request):
    return render(request, 'users/user/dashboard.html', {'section': 'profile',})


@login_required
def edit_details(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
    else:
        user_form = UserEditForm(instance=request.user)

    return render(request, 'users/user/edit_details.html', {'user_form': user_form})


@login_required
def delete_user(request):
    user = CustomUser.objects.get(user_name=request.user)
    # we are inactivating the user instead of deleting the whole user
    user.is_active = False
    user.save()
    logout(request)
    return redirect('users:delete_confirmation')


def account_register(request):
    if request.user.is_authenticated:
        return render(request, 'users/user/dashboard.html')
    
    if request.method == 'POST':
        registerForm = RegistrationForm(request.POST)
        if registerForm.is_valid():
            user = registerForm.save(commit=False)
            user.username = registerForm.cleaned_data['user_name']
            user.email = registerForm.cleaned_data['email']
            user.set_password(registerForm.cleaned_data['password'])
            user.is_active = False
            user.save()
            # 
            current_site = get_current_site(request)
            subject = 'activate your account'
            message = render_to_string('users/registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject=subject, message=message)
            return render(request, 'users/registration/email_verification_sent.html')
    else:
        registerForm = RegistrationForm()
    return render(request, 'users/registration/register.html', {'form': registerForm})


def account_activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except:
        pass
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('users:dashboard')
    else:
        return render(request, 'users/registration/activation_invalid.html')


# forgot password
def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email__exact=email)

            # reset password email
            current_site = get_current_site(request)
            subject = 'Reset Your Password'
            message = render_to_string('users/user/reset_password.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject=subject, message=message)
            return redirect('users:login')

        else:
            messages.error(request, 'Account does not exist')
            return redirect('users:forgotPassword')

    return render(request, 'users/user/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except:
        pass
    if user is not None and account_activation_token.check_token(user, token):
        request.session['uid'] = uid
        return redirect('users:login')
    else:
        messages.error(request, 'This link has been expired')
        return redirect('users:login')
        # return render(request, 'users/registration/activation_invalid.html')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = CustomUser.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset succesfully!')
            return redirect('users:login')
        else:
            messages.error(request, 'Password doenst match')
            return redirect('users:resetPassword')
    else:
        return render(request, 'users/user/resetpassword.html')