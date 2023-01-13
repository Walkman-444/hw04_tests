import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author_client = Client()
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        '''при отправке валидной формы со страницы
        создания поста создаётся новая запись в базе данных
        '''
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image=form_data['image'],
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
        self.assertRedirects(
            response, reverse('posts:post_detail', args=({self.post.pk})))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(modified_post.text, form_data['text'])
        self.assertEqual(modified_post.group.pk, form_data['group'])

    def test_can_be_written_by_an_authorized_user(self):
        '''комментировать посты может только авторизованный пользователь'''
        comments_count = Comment.objects.count()
        comment_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', args=(self.post.pk,)),
            data=comment_data,
            follow=True
        )
        last_comment = response.context['comments'][0]
        self.assertRedirects(
            response, reverse('posts:post_detail', args=({self.post.pk})))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(last_comment.text, comment_data['text'])
        self.assertEqual(last_comment.post, self.post)
        self.assertEqual(last_comment.author, self.user)
