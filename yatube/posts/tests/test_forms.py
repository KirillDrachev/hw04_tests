from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Group, Post


User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.owner_client = Client()
        self.owner_client.force_login(self.owner)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
        }
        response = self.owner_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'auth'}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group
            ).exists()
        )

    def test_edit_post(self):
        self.post = Post.objects.create(
            author=self.owner,
            text='Тестовый пост',
            group=self.group,
        )
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст 2',
        }
        response = self.owner_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': 1}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2',
                group=self.group
            ).exists()
        )
