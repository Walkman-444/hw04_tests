from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostFormsTests(TestCase):
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

    def test_create_post(self):
        '''при отправке валидной формы со страницы
        создания поста создаётся новая запись в базе данных
        '''
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'author': self.post.author
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=form_data['author'],
                group=form_data['group']
            ).exists()
        )

    def test_post_edit(self):
        '''при отправке валидной формы со страницы
        редактирования поста происходит изменение поста
        '''
        post_count = Post.objects.count()
        form_data = {
            'text': 'Редактируем тестовый пост',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.pk})),
            data=form_data,
            follow=True
        )
        modified_post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse('posts:post_detail', args=({self.post.pk})))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(modified_post.text, form_data['text'])
        self.assertEqual(modified_post.group.pk, form_data['group'])
