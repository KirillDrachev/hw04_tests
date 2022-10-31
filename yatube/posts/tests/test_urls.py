from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post


User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.owner_client = Client()
        self.owner_client.force_login(StaticURLTests.owner)

        self.authorized_client = Client()
        self.user = User.objects.create_user(username='user')
        self.authorized_client.force_login(self.user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

    def test_url_exists_and_redirect(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)
        post_pk = str(StaticURLTests.post.pk) + '/'
        group_slug = str(StaticURLTests.group.slug) + '/'
        user_name = str(StaticURLTests.owner.username) + '/'
        # Test data for the whole upp
        URL_test_data = {
            '/': ['everyone', 'posts/index.html'],
            '/group/' + group_slug: ['everyone', 'posts/group_list.html'],
            '/profile/' + user_name: ['everyone', 'posts/profile.html'],
            '/posts/' + post_pk: ['everyone', 'posts/post_detail.html'],
            '/posts/' + post_pk + 'edit/': ['owner', 'posts/create_post.html'],
            '/create/': ['authorized', 'posts/create_post.html'],
        }
        for url, data in URL_test_data.items():
            # Does page exist?
            with self.subTest(test=url + ' exists?'):
                response = self.owner_client.get(url)
                self.assertEqual(response.status_code, 200)
            # Template test
            with self.subTest(test=url + ' template'):
                response = self.owner_client.get(url)
                self.assertTemplateUsed(response, data[1])

            if data[0] == 'authorized' or data[0] == 'owner':
                # Redirect test for guest
                with self.subTest(test=url + ' not authorized redirect'):
                    response = self.guest_client.get(url, follow=True)
                    self.assertRedirects(response, '/auth/login/?next=' + url)

            if data[0] == 'owner':
                # Redirect test for authorized user
                with self.subTest(test=url + ' not owner redirect'):
                    response = self.authorized_client.get(url, follow=True)
                    self.assertRedirects(response, '/posts/' + post_pk)

    def test_url_404(self):
        response = self.owner_client.get('/None/')
        self.assertEqual(response.status_code, 404)
