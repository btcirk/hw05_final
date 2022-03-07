from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm

POSTS_ON_PAGE = 10


def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    posts_list = Post.objects.all()
    paginator = Paginator(posts_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_list(request):
    template = 'posts/group_list.html'
    title = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = Post.objects.filter(group=group).all()
    paginator = Paginator(posts_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = Post.objects.filter(author=author).all()
    paginator = Paginator(posts_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    post_count = paginator.count
    following = User.is_authenticated and author.following.exists()
    show_follow_btn = bool(request.user != author)
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_count': post_count,
        'following': following,
        'show_follow_btn': show_follow_btn
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_preview = post.text[:30]
    post_count = Post.objects.filter(author=post.author).count()
    form = PostForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    comment_form = CommentForm(request.POST or None)
    if post.author == request.user:
        is_author = True
    else:
        is_author = False
    context = {
        'post': post,
        'post_preview': post_preview,
        'post_count': post_count,
        'is_author': is_author,
        'form': form,
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required()
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required()
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': True, }
                  )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user).values_list(
        'author_id', flat=True
    )
    posts_list = Post.objects.filter(author_id__in=authors)
    paginator = Paginator(posts_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'follow': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (
            Follow.objects.filter(author=author, user=request.user).exists()
            or request.user == author
    ):
        return redirect('posts:profile', username=username)
    Follow.objects.create(author=author, user=request.user)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username=username)
