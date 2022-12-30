from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from django.urls import reverse
from django import forms

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.author_client.force_login(cls.post.author)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html'
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы (в нём передаётся форма)
    def test_homepage_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_group_list_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_profile_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:profile', args={self.user})
        )
        expected = list(Post.objects.filter(author=self.user)[:10])
        self.assertEqual(list(response.context['page_obj']), expected)

    def test_post_detail_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_create_edit_show_correct_context(self):
        '''Шаблон create_edit сформирован с правильным контекстом.'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        '''Шаблон create_post сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        '''Проверяем, что если при создании поста указать группу,
        то этот пост появляется:
        '''
        form_fields = {
            # на главной странице
            reverse('posts:index'),
            # на странице выбраной группы
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            # в профиле пользователя
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ),
        }
        for value in form_fields:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get('page_obj')[0]
                self.assertEqual(form_field, self.post)

    def test_check_group_not_in_mistake_group_list_page(self):
        '''Проверяем, что этот пост не попал в группу,
        для которой не был предназначен
        '''
        form_fields = {
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author_client = Client()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.posts_count = 13
        cls.posts = Post.objects.bulk_create([Post(
            id=id,
            author=cls.user,
            text='Тестовый пост',
            group=cls.group) for id in range(cls.posts_count)
        ])
        cls.paginator_context_names = {
            'index': '/',
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.user}/'
        }

    def test_paginator_correct_context(self):
        """index, group_list, profile содержат 10 постов на первой странице"""
        for name, url in self.paginator_context_names.items():
            with self.subTest(name=name):
                response = self.client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_correct_context_2(self):
        """index, group_list, profile содержат 3 поста на второй странице"""
        for name, url in self.paginator_context_names.items():
            with self.subTest(name=name):
                response = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
