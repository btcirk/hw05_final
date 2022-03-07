from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Post, Group

from http import HTTPStatus
from faker import Faker

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake = Faker()
        cls.user = User.objects.create_user(username=cls.fake.last_name())
        cls.author = User.objects.create_user(username=cls.fake.last_name())
        cls.group = Group.objects.create(
            title=cls.fake.text(),
            slug=cls.fake.slug(),
            description=cls.fake.text(),
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=cls.fake.paragraph(),
            group=cls.group,
        )
        cls.post_url = f'/posts/{cls.post.pk}/'
        cls.post_edit_url = f'/posts/{cls.post.pk}/edit/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.author.username}/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'),
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (cls.post_edit_url, 'posts/create_post.html')
        )
        cls.unexisting_url = '/unexisting_page/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_url_uses_correct_template(self):
        """URL использует нужный шаблон."""
        for url, template in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
        for url, template in self.private_urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location_for_guest(self):
        """Доступность страниц для анонимного пользователя."""
        for url in self.public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url[0])
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for url in self.private_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url[0])
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.guest_client.get(self.unexisting_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_at_desired_location_for_authorized(self):
        """Доступность страниц для авторизованного пользователя."""
        response = self.authorized_client.get(self.private_urls[0][0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_for_author(self):
        """Доступность страниц для автора."""
        response = self.author_client.get(self.post_edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_for_guest(self):
        """Редирект неавторизованного пользователя на страницу авторизации."""
        for url in self.private_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url[0], follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + url[0])

    def test_url_redirect_for_authorized(self):
        """Редирект авторизованного пользователя на страницу поста."""
        response = self.authorized_client.get(self.post_edit_url, follow=True)
        self.assertRedirects(response, self.post_url)
