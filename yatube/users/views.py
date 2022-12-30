from .forms import CreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправляем
    # пользователя на страницу авторизации.
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'
