import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post
from ..views import POST_COUNT

User = get_user_model()

FULL_NUMBER_OF_POSTS = 10
REMAINING_POSTS = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='HasNoName',
        )
        cls.user_2 = User.objects.create_user(
            username='author',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': cls.uploaded,
        }
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user,
        )
        cls.author_client.force_login(cls.post.author)

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
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

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_homepage_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        response = self.authorized_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:POST_COUNT])
        self.assertEqual(list(response.context['page_obj']), expected)
        expected_2 = response.context['page_obj'][0]
        image_in_post = expected_2.image
        self.assertEqual(image_in_post, self.post.image)

    def test_group_list_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(Post.objects.filter(
            group_id=self.group.id)[:POST_COUNT])
        self.assertEqual(list(response.context['page_obj']), expected)
        expected_2 = response.context['page_obj'][0]
        image_in_post = expected_2.image
        self.assertEqual(image_in_post, self.post.image)

    def test_profile_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        response = self.client.get(
            reverse('posts:profile', args={self.user})
        )
        expected = list(Post.objects.filter(author=self.user)[:POST_COUNT])
        self.assertEqual(list(response.context['page_obj']), expected)
        expected_2 = response.context['page_obj'][0]
        image_in_post = expected_2.image
        self.assertEqual(image_in_post, self.post.image)

    def test_post_detail_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        expected = response.context['post']
        self.assertEqual(expected.pk, self.post.pk)
        expected_2 = response.context['post']
        image_in_post = expected_2.image
        self.assertEqual(image_in_post, self.post.image)

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
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
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

    def test_post_detail_has_comment(self):
        '''после успешной отправки комментарий появляется на странице поста'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        for comment in response.context['comments']:
            if comment == self.comment:
                self.assertEqual(comment, self.comment)

    def test_cache(self):
        '''проверка кеширования главной страницы'''
        new_post = Post.objects.create(
            group=self.group,
            author=self.user,
            text=self.post.text
        )
        response = self.client.get(
            reverse('posts:index')
        )
        new_post.delete()
        response_2 = self.client.get(
            reverse('posts:index')
        )
        self.assertEqual(response.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response.content, response_3.content)

    def test_follow(self):
        '''Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок'''
        self.authorized_client.get(
            reverse(
                'posts:profile_follow', kwargs={'username': self.user_2})
        )
        self.assertEqual(
            Follow.objects.filter(author=self.user_2).exists(),
            True
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user_2})
        )
        self.assertEqual(
            Follow.objects.filter(author=self.user_2).exists(),
            False
        )

    def test_new_post_show(self):
        '''Новая запись пользователя появляется в ленте тех,
        кто на него подписан.
        '''
        Follow.objects.create(
            user=self.user,
            author=self.user_2,
        )
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user_2
        )
        response_auth = self.authorized_client.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertIn(post, response_auth)

    def test_new_post_not_show(self):
        '''Новая запись не появляется в ленте тех,
        кто не подписан.
        '''
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user_2
        )
        response_not_auth = self.authorized_client.get(
            reverse('posts:follow_index')
        ).context['page_obj']
        self.assertNotIn(post, response_not_auth)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
                self.assertEqual(len(response.context['page_obj']),
                                 FULL_NUMBER_OF_POSTS)

    def test_paginator_correct_context_2(self):
        """index, group_list, profile содержат 3 поста на второй странице"""
        for name, url in self.paginator_context_names.items():
            with self.subTest(name=name):
                response = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 REMAINING_POSTS)
