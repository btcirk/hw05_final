from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from ..models import Post, Group, Follow
from ..views import POSTS_ON_PAGE

from faker import Faker
import shutil
import tempfile

User = get_user_model()
POSTS_ON_SECONG_PAGE = 3
NUM_OF_POSTS = POSTS_ON_PAGE + POSTS_ON_SECONG_PAGE
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
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
        cls.image = SimpleUploadedFile(
            name='image.jpeg',
            content=cls.fake.image(size=(1024, 768), image_format='jpeg'),
            content_type='image/jpeg'
        )
        Post.objects.bulk_create([
            Post(
                text=cls.fake.paragraph(),
                author=cls.author,
                group=cls.group,
                image=cls.image
            )
            for _ in range(NUM_OF_POSTS)
        ])
        cls.post = Post.objects.get(pk=NUM_OF_POSTS)

        cls.index_url = ('posts:index',
                         None,
                         'posts/index.html',)
        cls.group_url = ('posts:group',
                         (cls.group.slug,),
                         'posts/group_list.html',)
        cls.profile_url = ('posts:profile',
                           (cls.author.username,),
                           'posts/profile.html',)
        cls.post_url = ('posts:post_detail',
                        (cls.post.pk,),
                        'posts/post_detail.html',)
        cls.post_new_url = ('posts:post_create',
                            None,
                            'posts/create_post.html',)
        cls.post_edit_url = ('posts:post_edit',
                             (cls.post.pk,),
                             'posts/create_post.html',)
        cls.profile_follow_url = ('posts:profile_follow',
                                  (cls.author.username,),
                                  'posts/profile.html')
        cls.profile_unfollow_url = ('posts:profile_unfollow',
                                    (cls.author.username,),
                                    'posts/profile.html')
        cls.feed_url = ('posts:follow_index',
                        None,
                        'posts/follow.html')
        cls.unexisting_url = ('/unexisting_page/', 'core/404.html')
        cls.urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url,
            cls.post_url,
            cls.post_new_url,
            cls.post_edit_url
        )
        cls.paginated_urls = (
            cls.index_url,
            cls.group_url,
            cls.profile_url
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """View использует правильный шаблон."""
        for url in self.urls:
            view, args, template = url
            with self.subTest(view=view, args=args, template=template):
                response = self.author_client.get(reverse(view, args=args))
                self.assertTemplateUsed(response, template)

    def test_pages_uses_pagination(self):
        """На страницах работает пагинация."""
        for url in self.paginated_urls:
            view, args, template = url
            with self.subTest(view=view, args=args, template=template):
                response = self.author_client.get(reverse(view, args=args))
                self.assertTrue(
                    len(response.context['page_obj']) == POSTS_ON_PAGE
                )
                response = self.guest_client.get(
                    reverse(view, args=args),
                    {'page': 2}
                )
                self.assertTrue(
                    len(response.context['page_obj']) == POSTS_ON_SECONG_PAGE)

    def test_index_page_show_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        view, args, _ = self.index_url
        response = self.guest_client.get(reverse(view, args=args))
        content = response.context['page_obj'][0]
        self.assertTrue('title' in response.context)
        self.assertTrue('page_obj' in response.context)
        self.assertEqual(content.image, self.post.image)

    def test_group_page_show_correct_context(self):
        """Шаблон постов группы сформирован с правильным контекстом."""
        view, args, _ = self.group_url
        response = self.guest_client.get(reverse(view, args=args))
        content = response.context['page_obj'][0]
        self.assertTrue('group' in response.context)
        self.assertTrue('page_obj' in response.context)
        self.assertEqual(content.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон профиля сформирован с ожидаемым контекстом."""
        view, args, _ = self.profile_url
        response = self.guest_client.get(reverse(view, args=args))
        content = response.context['page_obj'][0]
        self.assertIn('author', response.context)
        self.assertIn('page_obj', response.context)
        self.assertIn('post_count', response.context)
        self.assertEqual(content.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон поста сформирован с ожидаемым контекстом."""
        view, args, _ = self.post_url
        response = self.guest_client.get(reverse(view, args=args))
        content = response.context['post']
        self.assertIn('post', response.context)
        self.assertIn('post_preview', response.context)
        self.assertIn('post_count', response.context)
        self.assertIn('is_author', response.context)
        self.assertEqual(content.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон создания поста сформирован с ожидаемым контекстом."""
        view, args, _ = self.post_new_url
        response = self.author_client.get(reverse(view, args=args))
        self.assertIn('form', response.context)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон редактирования поста сформирован с ожидаемым контекстом."""
        view, args, _ = self.post_edit_url
        response = self.author_client.get(reverse(view, args=args))
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)

    def test_post_exists_on_index_page(self):
        """Последний созданный пост присутствует на главной странице."""
        view, args, _ = self.index_url
        response = self.guest_client.get(reverse(view, args=args))
        self.assertEqual(self.post.text,
                         response.context.get('page_obj').object_list[0].text)

    def test_post_exists_on_group_page(self):
        """Последний созданный пост присутствует на странице группы постов."""
        view, args, _ = self.group_url
        response = self.guest_client.get(reverse(view, args=args))
        self.assertEqual(self.post.text,
                         response.context.get('page_obj').object_list[0].text)

    def test_post_exists_on_profile_page(self):
        """Последний созданный пост присутствует в профайле автора."""
        view, args, _ = self.profile_url
        response = self.guest_client.get(reverse(view, args=args))
        self.assertEqual(self.post.text,
                         response.context.get('page_obj').object_list[0].text)

    def test_post_exist_in_group(self):
        """При создании пост попадает в нужную группу."""
        group_new = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-slug',
        )
        post_new = Post.objects.create(
            author=self.author,
            group=group_new,
            text='Это новый тестовый пост',
        )
        view, args, _ = self.group_url
        response = self.guest_client.get(
            reverse(view, args=(group_new.slug,)))
        self.assertEqual(
            post_new.text,
            response.context.get('page_obj').object_list[0].text
        )
        response = self.guest_client.get(reverse(view, args=args))
        self.assertNotEqual(
            post_new.text,
            response.context.get('page_obj').object_list[0].text
        )

    def test_cache_index_page(self):
        """Кеширование на главной странице работает."""
        view, args, _ = self.index_url
        response = self.guest_client.get(reverse(view, args=args))
        res_1 = response.content
        post = Post.objects.get(pk=self.post.pk)
        post.delete()
        response = self.guest_client.get(reverse(view, args=args))
        res_2 = response.content
        self.assertTrue(res_1 == res_2)
        cache.clear()
        response = self.guest_client.get(reverse(view, args=args))
        res_2 = response.content
        self.assertTrue(res_1 != res_2)

    def test_404_use_custom_template(self):
        """Страница 404 отдает кастомный шаблон."""
        url, template = self.unexisting_url
        response = self.guest_client.get(url)
        self.assertTemplateUsed(response, template)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписаться и удалять подписку."""
        before_follow = Follow.objects.filter(user=self.user,
                                              author=self.author).count()
        view, args, _ = self.profile_follow_url
        _ = self.authorized_client.get(reverse(view, args=args))
        after_follow = Follow.objects.filter(user=self.user,
                                             author=self.author).count()
        self.assertEqual(after_follow, before_follow + 1)
        view, args, _ = self.profile_unfollow_url
        _ = self.authorized_client.get(reverse(view, args=args))
        after_unfollow = Follow.objects.filter(user=self.user,
                                               author=self.author).count()
        self.assertEqual(after_unfollow, before_follow)

    def test_guest_user_cant_follow(self):
        """Неавторизованный пользователь не может подписаться."""
        before_follow = Follow.objects.all().count()
        view, args, _ = self.profile_follow_url
        response = self.guest_client.get(reverse(view, args=args))
        after_follow = Follow.objects.all().count()
        self.assertEqual(after_follow, before_follow)
        self.assertRedirects(
            response,
            '/auth/login/?next=' + f'/profile/{self.author.username}/follow/'
        )

    def test_user_cant_follow_yourself(self):
        """Нельзя подписаться на самого себя."""
        follows_before = Follow.objects.all().count()
        view, _, _ = self.profile_follow_url
        _ = self.authorized_client.get(
            reverse(view, args=(self.user.username,)))
        follows_after = Follow.objects.all().count()
        self.assertEqual(follows_before, follows_after)

    def test_post_appears_in_followers_feed(self):
        """Посты отображаются в ленте фолловеров."""
        user_ = User.objects.create_user(username=self.fake.last_name())
        follower_client = Client()
        follower_client.force_login(user_)
        view, args, _ = self.profile_follow_url
        follower_client.get(reverse(view, args=args))
        post_new = Post.objects.create(
            author=self.author,
            group=self.group,
            text=self.fake.paragraph(),
        )
        view, _, _ = self.feed_url
        response_follower = follower_client.get(reverse(view))
        response_user = self.authorized_client.get(reverse(view))
        self.assertEqual(
            post_new.text,
            response_follower.context.get('page_obj').object_list[0].text
        )
        self.assertFalse(response_user.context['page_obj'].object_list)
