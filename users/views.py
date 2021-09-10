from django.http.response import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib import messages

from carts.models import Cart, CartItem
from .models import CustomUser
from .forms import RegistrationForm, UserEditForm
from .forms import (UserLoginForm)
from .tokens import account_activation_token
from carts.views import _cart_id

import requests


from django.contrib.auth import authenticate



def login_view(request):

    if request.user.is_authenticated:
        return render(request, 'users/user/dashboard.html')

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                try:
                    cart = Cart.objects.get(cart_id=_cart_id(request))
                    is_cart_item_exists = CartItem.objects.filter(cart=cart).exists() 
                    if is_cart_item_exists:
                        cart_item = CartItem.objects.filter(cart=cart)

                        product_variation = []
                        for item in cart_item:
                            variation = item.variation.all()
                            product_variation.append(list(variation))

                        # get the cart items from the user to access his product variation
                        cart_item = CartItem.objects.filter(user=user)

                        ex_var_list = []
                        id = []
                        for item in cart_item:
                            existing_variation = item.variation.all()
                            ex_var_list.append(list(existing_variation))
                            id.append(item.id)
                        

                        for pr in product_variation:
                            if pr in ex_var_list:
                                index = ex_var_list.index(pr)
                                item_id = id[index]
                                item = CartItem.objects.get(id=item_id)
                                item.quantity += 1
                                # assing the user
                                item.user = user
                                # save the item
                                item.save()
                            else:
                                cart_item = CartItem.objects.filter(cart=cart)
                                for item in cart_item:
                                    item.user = user
                                    item.save()

                except:
                    pass
                login(request, user)
                # messages.info(
                #     request, f"You are now logged in as {email}.")
                url = request.META.get('HTTP_REFERER')
                try:
                    query = requests.utils.urlparse(url).query
                    # 
                    params = dict(x.split('=') for x in query.split('&'))
                    if 'next' in params:
                        nextPage = params['next']
                        return redirect(nextPage)
                
                except:
                    return redirect("users:dashboard")
            
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    form = UserLoginForm()
    return render(request, "users/registration/login.html", context={"form": form})


   


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
