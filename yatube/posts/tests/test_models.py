from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, POSTS_COUNT, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        test_post = self.post
        post_str = str(test_post)
        expected_test_post = test_post.text[:POSTS_COUNT]
        self.assertEqual(expected_test_post, post_str)

        test_group = self.group
        group_str = str(test_group)
        expected_test_group = test_group.title
        self.assertEqual(expected_test_group, group_str)

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        test_post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).verbose_name, expected)

    def test_group_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        test_post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).help_text, expected)
