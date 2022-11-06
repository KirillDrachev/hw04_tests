from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


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
        cls.post = Post.objects.create(
            author=cls.owner,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.field_value = {
            'author': cls.owner,
            'group': cls.group,
            'count': 1,
            'post': cls.post,
            'page_obj': cls.post,
        }

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

    def _test_form_correct_context(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
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
