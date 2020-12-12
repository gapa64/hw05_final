from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Post, Group, Follow


User = get_user_model()


def index(request):
    latest = Post.objects.all()
    paginator = Paginator(latest, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page,
                                          'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group,
                                          'page': page,
                                          'paginator': paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', {'form': form})
    form = PostForm()
    return render(request, 'new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    author_posts = author.posts.all()
    paginator = Paginator(author_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {'author': author,
                                            'following': following,
                                            'page': page,
                                            'paginator': paginator})


def post_view(request, username, post_id):
    post = get_object_or_404(Post,
                             pk=post_id,
                             author__username=username)
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'post.html', {'author': post.author,
                                         'comments': comments,
                                         'post': post,
                                         'form': form})


@login_required
def post_edit(request, username, post_id):
    original_post = get_object_or_404(Post,
                                      pk=post_id,
                                      author__username=username)
    if request.user != original_post.author:
        return redirect('post', username=username, post_id=post_id)
    bound_form = PostForm(request.POST or None,
                          files=request.FILES or None,
                          instance=original_post)
    if bound_form.is_valid():
        updated_post = bound_form.save(commit=False)
        updated_post.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {'form': bound_form,
                                             'post': original_post})


@login_required()
def add_comment(request, username, post_id):
    commented_post = get_object_or_404(Post,
                                       pk=post_id,
                                       author__username=username)
    comment_form = CommentForm(request.POST or None)
    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.author = request.user
        comment.post = commented_post
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    following_posts = Post.objects.filter(author__following__user=request.user).all()
    paginator = Paginator(following_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page,
                                           'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        if not author.following.filter(user=request.user).exists():
            Follow.objects.create(user=request.user,
                                  author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    binding = Follow.objects.filter(author__username=username,
                                    user=request.user)
    if binding.exists():
        binding.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )

def server_error(request):
    return render(request, 'misc/500.html', status=500)
