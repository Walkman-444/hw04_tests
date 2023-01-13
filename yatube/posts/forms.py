from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {'text': 'Введите текст', 'group': 'Выберите группу'}
        help_text = {'text': 'Любой текст', 'group': 'Из уже существующих'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Введите текст'}
        help_text = {'text': 'Любой текст'}
