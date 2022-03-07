from django.urls import reverse
from django.test import TestCase, Client
from http import HTTPStatus


class AboutTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_uses_correct_templates(self):
        """URL-адресам about соответсвуют нужные шаблоны."""
        url_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_about_urls_exists_at_desired_locations(self):
        """Доступность страниц приложения аbout."""
        urls = ('/about/author/', '/about/tech/')
        for url in urls:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_views_uses_correct_templates(self):
        """View-классы about используют нужные шаблоны."""
        url_templates = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
