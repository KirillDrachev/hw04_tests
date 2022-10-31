from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .forms import PostForm
from .models import Group, Post, User
from .utils import by_page


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = by_page(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = by_page(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    count = post_list.count()
    page_obj = by_page(request, post_list)
    context = {
        'author': author,
        'count': count,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    count = post.author.posts.count()
    context = {
        'count': count,
        'post': post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    post_form = PostForm(request.POST or None)
    if request.method == 'POST' and post_form.is_valid():
        post = post_form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse_lazy('posts:profile',
                                     args=[request.user.username]))
    return render(request, template, {'form': post_form, 'is_edit': False})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect(reverse_lazy('posts:post_detail', args=[post.pk]))
    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save()
            return redirect(reverse_lazy('posts:post_detail', args=[post.pk]))
    post_form = PostForm(instance=post)
    return render(request, template, {'form': post_form, 'is_edit': True})
