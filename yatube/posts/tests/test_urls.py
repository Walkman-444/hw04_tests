from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):
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

    # Тестирование общедоступных страниц
    def test_home_page(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page(self):
        response = self.guest_client.get('/group/test_slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_page(self):
        response = self.guest_client.get(f"/profile/{self.user}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_page(self):
        response = self.guest_client.get(f"/posts/{self.post.pk}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Запрос к несуществующей странице
    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Тестирование страниц доступных автору
    def test_edit_post_by_author(self):
        response = self.author_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Тестирование страниц доступных не автору
    def test_edit_post_by_not_author(self):
        response = self.guest_client.get(
            f"/posts/{self.post.pk}/edit/", follow=True)
        self.assertRedirects(response,
                             f"/auth/login/?next=/posts/{self.post.pk}/edit/"),

    # Тестирование страниц доступных авторизованному пользователю
    def test_create_page(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Тестирование шаблонов
    # Тестирование шаблонов неавторизованного пользователя
    def test_unauthorized_templates_use(self):
        public_urls = {
            'posts/index.html': '/',
            'posts/group_list.html': f"/group/{self.group.slug}/",
            'posts/profile.html': f"/profile/{self.user}/",
            'posts/post_detail.html': f"/posts/{self.post.pk}/",
        }
        for template, url in public_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    # Тестирование шаблонов авторизованного пользователя
    def test_authorized_templates_use(self):
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

    # Тестирование шаблона для автора поста
    def test_post_author_template_use(self):
        response = self.author_client.get(f"/posts/{self.post.pk}/edit/")
        self.assertTemplateUsed(response, 'posts/post_create.html')
