from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from ..models import Group, Post


User = get_user_model()


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

    def test_pages_show_correct_context(self):
        field_value = {
            'author': self.owner,
            'group': self.group,
            'count': 1,
            'post': self.post,
            'page_obj': self.post,
            'is_edit': True,
        }
        pages_names_context_fields = {
            reverse('posts:index'): ['page_obj'],
            reverse('posts:group_posts',
                    kwargs={'slug': 'test_slug'}): ['group', 'page_obj'],
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): ['author', 'count',
                                                   'page_obj'],
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): ['count', 'post'],
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): ['form'],
            reverse('posts:post_create'): ['form'],
        }
        for reverse_name, field_list in pages_names_context_fields.items():
            response = self.owner_client.get(reverse_name)
            for field in field_list:
                with self.subTest(reverse_name=reverse_name + ' ' + field):
                    if field == 'form':
                        self.Test_form_correct_context(response)
                    elif field == 'page_obj':
                        self.Test_post_correct_context(
                            response.context['page_obj'][0]
                        )
                    elif field == 'post':
                        self.Test_post_correct_context(
                            response.context.get('post')
                        )
                    else:
                        self.assertEqual(response.context.get(field),
                                         field_value[field])

    def Test_post_correct_context(self, post):
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.author.pk, self.owner.pk)
        self.assertEqual(post.group.pk, self.group.pk)

    def Test_form_correct_context(self, response):
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
