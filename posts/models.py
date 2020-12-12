from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Group(models.Model):

    title = models.CharField(max_length=200,
                             verbose_name='Название группы')
    slug = models.SlugField(unique=True,
                            max_length=79,
                            verbose_name='Slug группы')
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):

    text = models.TextField(verbose_name='Текст публикации',
                            help_text='Введите текст публикации')
    pub_date = models.DateTimeField(verbose_name='Дата публикации',
                                    auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор')
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              help_text='Добавьте группу если хотите, '
                                        'но вообще это не обязательно!',
                              blank=True,
                              null=True)
    image = models.ImageField(upload_to='posts/',
                              blank=True,
                              null=True,
                              verbose_name='Изображение')

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Коментатор')
    created = models.DateTimeField(verbose_name='Дата создания',
                                   auto_now_add=True)
    post = models.ForeignKey(Post,
                             on_delete=models.CASCADE,
                             related_name='comments',
                             help_text='Добавьте Ваш комментарий')
    text = models.TextField(verbose_name='Текст публикации',
                            help_text='Введите текст публикации')


class Follow(models.Model):

    user = models.ForeignKey(User,
                             related_name='follower',
                             on_delete=models.CASCADE,
                             verbose_name='Подписался кто')

    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE,
                               verbose_name='Подписан на кого')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_follow')
        ]
