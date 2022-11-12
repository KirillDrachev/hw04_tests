from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.owner = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.owner,
            text='Тестовый пост 123456 abc',
        )

    def setUp(self):
        self.guest_client = Client()

        self.owner_client = Client()
        self.owner_client.force_login(self.owner)

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_url_exists(self):
        URL_test_data = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.owner.username}/',
            f'/posts/{self.post.pk}/',
        ]
        for url in URL_test_data:
            with self.subTest(test=url + ' exists?'):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_redirect(self):
        URL_test_data = [
            f'/posts/{self.post.pk}/edit/',
            '/create/',
            f'/posts/{self.post.pk}/comment/',
        ]
        for url in URL_test_data:
            with self.subTest(test=url + ' not authorized redirect'):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_authorized_redirect(self):
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/',
                                              follow=True)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_authorized_url_exists(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_owner_url_exists(self):
        response = self.owner_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_templates(self):
        URL_test_data = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.owner.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in URL_test_data.items():
            with self.subTest(test=url + ' template'):
                response = self.owner_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_url_404(self):
        response = self.owner_client.get('/None/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
