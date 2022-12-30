from django.contrib.auth.views import (LoginView,
                                       LogoutView,
                                       PasswordChangeView,
                                       PasswordChangeDoneView,
                                       PasswordResetView,
                                       PasswordResetDoneView,
                                       PasswordResetConfirmView,
                                       PasswordResetCompleteView)
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    # Страница регистрации - auth/signup/
    path('signup/', views.SignUp.as_view(), name='signup'),
    # Шаблон, который отображает возвращаемую страницу.
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    # Страница входа в учётную запись
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    # Необязательные задания
    # Смена пароля: задать новый пароль
    path(
        'password_change/',
        PasswordChangeView.as_view(
            template_name='users/password_change_form.html'),
        name='password_change_form'
    ),
    # Смена пароля: уведомление об удачной смене пароля
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'
    ),
    # Восстановление пароля:
    # форма для восстановления пароля через email
    path(
        'password_reset/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html'),
        name='password_reset_form'
    ),
    # Восстановление пароля:
    # уведомление об отправке
    # ссылки для восстановления пароля на email
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'
    ),
    # Восстановление пароля:
    # страница подтверждения сброса пароля;
    # пользователь попадает сюда по ссылке из письма
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'),
        name='password_reset_confirm.'
    ),
    # Восстановление пароля:
    # уведомление о том, что пароль изменен
    path(
        'password_reset/done/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]
