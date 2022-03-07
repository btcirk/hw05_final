from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from ..models import Post, Group, Comment

from faker import Faker
import shutil
import tempfile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake = Faker()
        cls.author = User.objects.create_user(username=cls.fake.last_name())
        cls.group = Group.objects.create(
            title=cls.fake.text(),
            slug=cls.fake.slug(),
            description=cls.fake.text(),
        )
        cls.image = SimpleUploadedFile(
            name='image.jpeg',
            content=cls.fake.image(size=(1024, 768), image_format='jpeg'),
            content_type='image/jpeg'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=cls.fake.paragraph(),
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_post_create_record_in_db(self):
        """При создании поста создается запись в БД
        и редирект на страницу профиля пользователя."""
        total_records = Post.objects.count()
        image = SimpleUploadedFile(
            name='image2.jpeg',
            content=self.fake.image(size=(1024, 768), image_format='jpeg'),
            content_type='image/jpeg'
        )
        form = {
            'text': self.fake.text(),
            'group': self.group.pk,
            'image': image
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), total_records + 1)
        self.assertTrue(Post.objects.filter(
            text=form['text'],
            group=form['group'],
            image='posts/' + image.name
        ).exists())
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.author.username,)),
        )

    def test_post_change_record_in_db(self):
        """При редактировании поста изменяется запись БД
        на нужный контекст переданной формы."""
        total_records = Post.objects.count()
        group_ = Group.objects.create(
            title=self.fake.text(),
            slug=self.fake.slug(),
            description=self.fake.text(),
        )
        form = {
            'text': self.fake.paragraph(),
            'group': group_.pk
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=(self.post.pk,)),
            data=form,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), total_records)
        self.assertTrue(Post.objects.filter(
            text=form['text'],
            group=form['group']
        ).exists())
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.pk,)),
        )

    def test_unauth_user_cant_publish_post(self):
        """Неавторизованный пользователь не может опубликовать пост."""
        total_records = Post.objects.count()
        form = {
            'text': self.fake.text(),
            'group': self.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form,
            follow=True,
        )
        self.assertNotEqual(Post.objects.count(), total_records + 1)
        self.assertFalse(Post.objects.filter(
            text=form['text'],
            group=form['group']
        ).exists())
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_unauth_user_cant_publish_comment(self):
        """Неавторизованный пользователь не может опубликовать комментарий."""
        total_records = Comment.objects.count()
        form = {
            'text': self.fake.text()
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form,
            follow=True,
        )
        self.assertNotEqual(Comment.objects.count(), total_records + 1)
        self.assertFalse(Comment.objects.filter(
            text=form['text'],
            post=self.post.pk
        ).exists())
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_comment_put_in_DB_and_shows_on_page(self):
        """После отправки комментарий попадает в БД и на страницу поста."""
        total_records = Comment.objects.count()
        form = {
            'text': self.fake.text()
        }
        response = self.author_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form,
            follow=True,
        )
        self.assertIn('form', response.context)
        last_comment = response.context['comments'][0]
        self.assertEqual(Comment.objects.count(), total_records + 1)
        self.assertTrue(Comment.objects.filter(
            text=form['text'],
            post=self.post.pk
        ).exists())
        self.assertEqual(form['text'], last_comment.text)
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/'
        )
        response = self.author_client.get(
            reverse('posts:post_detail', args=(self.post.pk,)))
        last_comment = response.context['comments'][0]
        self.assertEqual(form['text'], last_comment.text)
