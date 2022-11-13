import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='another_test_slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.owner,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.field_value = {
            'author': cls.owner,
            'group': cls.group,
            'count': 1,
            'post': cls.post,
            'page_obj': cls.post,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner_client = Client()
        self.owner_client.force_login(self.owner)

    def test_pages_uses_correct_template(self):
        pages_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.owner_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        response = self.owner_client.get(reverse('posts:index'))
        self._test_post_correct_context(response.context['page_obj'][0])

    def test_group_context(self):
        response = self.owner_client.get(reverse('posts:group_posts',
                                         kwargs={'slug': self.group.slug}))

        self._test_post_correct_context(response.context['page_obj'][0])

        self.assertEqual(response.context.get('group'),
                         self.field_value['group'])

    def test_post_context(self):
        response = self.owner_client.get(reverse('posts:profile',
                                         kwargs={'username': 'auth'}))

        self._test_post_correct_context(response.context['page_obj'][0])

        self.assertEqual(response.context.get('author'),
                         self.field_value['author'])

        self.assertEqual(response.context.get('count'),
                         self.field_value['count'])

    def test_detail_context(self):
        response = self.owner_client.get(reverse('posts:post_detail',
                                         kwargs={'post_id': 1}))

        self._test_post_correct_context(response.context['post'])
        self.assertEqual(response.context.get('count'),
                         self.field_value['count'])

    def test_edit_context(self):
        response = self.owner_client.get(reverse('posts:post_edit',
                                         kwargs={'post_id': 1}))

        self._test_form_correct_context(response)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_create_context(self):
        response = self.owner_client.get(reverse('posts:post_create'))

        self._test_form_correct_context(response)
        self.assertEqual(response.context.get('is_edit'), False)

    def _test_post_correct_context(self, post):
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.author.pk, self.owner.pk)
        self.assertEqual(post.group.pk, self.group.pk)
        self.assertEqual(post.image, 'posts/small.gif')

    def _test_form_correct_context(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_post_added_correctly(self):
        reverse_name = reverse('posts:group_posts',
                               kwargs={'slug': 'another_test_slug'})
        response = self.owner_client.get(reverse_name)
        self.assertEqual(len(response.context['page_obj']), 0)


class PostPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(0, 13):
            cls.post = Post.objects.create(
                author=cls.owner,
                text='Тестовый пост' + str(i),
                group=cls.group,
            )

    def setUp(self):
        self.owner_client = Client()
        self.owner_client.force_login(self.owner)

    def test_pages_paginator(self):
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': 'test_slug'}),
            reverse('posts:profile',
                    kwargs={'username': 'auth'}),
        ]
        for page in pages_names:
            with self.subTest(page_name=page):
                response = self.owner_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)
            with self.subTest(page_name=page + '?page=2'):
                response = self.owner_client.get(page + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follow_user(self):
        Follow.objects.all().delete()
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[self.author]),
            follow=True
        )
        self.assertTrue(
            Follow.objects.filter(author=self.author, user=self.user).exists()
        )

    def test_unfollow_user(self):
        Follow.objects.all().delete()
        Follow.objects.create(
            user=self.user, author=self.author
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=[self.author]),
            follow=True)
        self.assertFalse(
            Follow.objects.filter(
                author=self.author, user=self.user).exists()
        )

    def test_new_post_for_follower(self):
        Follow.objects.all().delete()
        Follow.objects.create(
            user=self.user, author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

        Follow.objects.all().delete()
        response_after_unfollowing = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            self.post, response_after_unfollowing.context['page_obj']
        )


class CacheTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_cache(self):
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        posts = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(posts, response.content)
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(posts, response.content)
