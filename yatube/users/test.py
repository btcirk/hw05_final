from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client
from django import forms

from http import HTTPStatus
from faker import Faker

User = get_user_model()


class UsersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake = Faker()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='JohnDoe')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_users_uses_correct_templates(self):
        """URL-адресам users соответсвуют нужные шаблоны."""
        url_templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html'
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_users_urls_exists_at_desired_locations(self):
        """Доступность страниц приложения аbout."""
        urls = (
            '/auth/signup/',
            '/auth/login/',
            '/auth/logout/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/done/',
        )
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

        urls = (
            '/auth/password_change/',
            '/auth/password_change/done/',
        )
        for url in urls:
            response = self.authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_users_views_uses_correct_templates(self):
        """View-классы about используют нужные шаблоны."""
        url_templates = {
            reverse('users:login'): 'users/login.html',
            reverse('users:signup'): 'users/signup.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:password_reset_form'): (
                'users/password_reset_form.html'),
            reverse('users:password_reset_done'): (
                'users/password_reset_done.html'),
            reverse('users:password_reset_complete'): (
                'users/password_reset_complete.html')
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_users_signup_page_show_correct_context(self):
        """Шаблон на странице регистрации сформирован с нужным контекстом."""
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_users_signup_create_record_in_db(self):
        total_records = User.objects.count()
        password = self.fake.password()
        form = {
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'username': self.fake.last_name(),
            'email': self.fake.email(),
            'password1': password,
            'password2': password
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form,
            follow=True,
        )
        self.assertEqual(User.objects.count(), total_records + 1)
        self.assertTrue(User.objects.filter(
            first_name=form['first_name'],
            last_name=form['last_name'],
            username=form['username'],
            email=form['email']
        ).exists())
        self.assertRedirects(
            response,
            reverse('posts:index'),
        )
