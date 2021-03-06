from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView

from . import views
from .forms import (UserLoginForm)

app_name = 'users'

urlpatterns = [
    # homepage
    path('', views.homeview, name='home'),
    # auth user
    # path('login/', auth_views.LoginView.as_view(template_name='users/registration/login.html',
    #                                             form_class=UserLoginForm), name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='users/registration/logout.html'), name='logout'),

    # registration
    path('register/', views.account_register, name='register'),
    path('activate/<slug:uidb64>/<slug:token>/', views.account_activate, name='activate'),
    # user dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    # orders
    path('my_orders/', views.my_orders, name='my_orders'),
    path('my_orders_detail/<int:order_id>/',
         views.my_orders_detail, name='my_orders_detail'),
    # 
    path('profile/edit/', views.edit_details, name='edit_details'),
    path('profile/delete_user/', views.delete_user, name='delete_user'),
    path('profile/delete_confirm/', TemplateView.as_view(
        template_name="users/user/delete_confirm.html"), name='delete_confirmation'),
    
    # password
    # path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    # path('resetpassword_validate/<slug:uidb64>/<slug:token>/',
    #      views.resetpassword_validate, name='resetpassword_validate'),
    # path('resetPassword/', views.resetPassword, name='resetPassword'),
]
