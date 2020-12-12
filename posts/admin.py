from django.contrib import admin

from .models import Post, Group, Follow, Comment


class PostAdmin(admin.ModelAdmin):

    list_display = ('text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):

    list_display = ('title', 'slug', 'description', )
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    list_filter = ('slug',)
    empty_value_display = '-пусто-'

class FollowAdmin(admin.ModelAdmin):

    list_display = ('user', 'author')
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
    empty_value_display = '-пусто-'

class CommentAdmin(admin.ModelAdmin):

    list_display = ('text', 'created', 'author', 'post')
    search_fields = ('text', 'created', )
    list_filter = ('author', 'author')
    empty_value_display = '-пусто-'

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment, CommentAdmin)
