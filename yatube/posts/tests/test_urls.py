from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.author_client.force_login(cls.post.author)
        cls.public_urls = {
            'posts/index.html': '/',
            'posts/group_list.html': f"/group/{cls.group.slug}/",
            'posts/profile.html': f"/profile/{cls.user}/",
            'posts/post_detail.html': f"/posts/{cls.post.pk}/",
        }

    def setUp(self):
        cache.clear()

    def test_home_page(self):
        '''Тестирование общедоступных страниц'''
        for template, url in self.public_urls.items():
            with self.subTest(template=template):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        '''Запрос к несуществующей странице'''
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_edit_post_by_author(self):
        '''Тестирование страниц доступных автору'''
        response = self.author_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post_by_not_author(self):
        '''Тестирование страниц доступных не автору'''
        response = self.client.get(
            f"/posts/{self.post.pk}/edit/", follow=True)
        self.assertRedirects(response,
                             f"/auth/login/?next=/posts/{self.post.pk}/edit/"),

    def test_create_page(self):
        '''Тестирование страниц доступных авторизованному пользователю'''
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauthorized_templates_use(self):
        '''Тестирование шаблонов неавторизованного пользователя'''
        for template, url in self.public_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)

    def test_authorized_templates_use(self):
        '''Тестирование шаблонов авторизованного пользователя'''
        unpublic_urls = {
            'posts/index.html': '/',
            'posts/group_list.html': f"/group/{self.group.slug}/",
            'posts/profile.html': f"/profile/{self.user}/",
            'posts/post_detail.html': f"/posts/{self.post.pk}/",
            'posts/post_create.html': '/create/'
        }
        for template, url in unpublic_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_author_template_use(self):
        '''Тестирование шаблона для автора поста'''
        response = self.author_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertTemplateUsed(response, 'posts/post_create.html')
