from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

from faker import Faker

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake = Faker()
        cls.user = User.objects.create_user(username=cls.fake.last_name())
        cls.group = Group.objects.create(
            title=cls.fake.text(),
            slug=cls.fake.slug(),
            description=cls.fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.fake.paragraph(),
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        vals = ((str(post), post.text[:15]), (str(group), group.title))
        for value, expected in vals:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
