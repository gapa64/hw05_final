import tempfile
import shutil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.models import Site
from django.db.models.query import QuerySet
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, Comment, Follow

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.small_gif = (
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.user = User.objects.create_user(username='panda')
        cls.user_wrong = User.objects.create_user(username='bear')
        cls.user_follower = User.objects.create_user(username='wolf')
        cls.user_following = User.objects.create_user(username='rabbit')

        cls.user_subscribed_to = Follow.objects.create(
                                     user=cls.user,
                                     author=cls.user_following)

        cls.subscribed_to_user = Follow.objects.create(
                                     user=cls.user_follower,
                                     author=cls.user)

        cls.group = Group.objects.create(title='pandas group',
                                         slug='pandas',
                                         description='Pandas stories')
        cls.group_wrong = Group.objects.create(title='bear group',
                                               slug='bear',
                                               description='bear stories')

        for i in range(1, 11):
            Post.objects.create(text=f'Про панду история {i}',
                                author=cls.user,
                                group=cls.group)

        cls.post = Post.objects.create(text='История про панду',
                                       author=cls.user,
                                       group=cls.group,
                                       image=cls.uploaded)
        cls.comment1 = Comment.objects.create(text='Первый коментарий',
                                              author=cls.user_wrong,
                                              post=cls.post)
        cls.comment2 = Comment.objects.create(text='Второй коментарий',
                                              author=cls.user_wrong,
                                              post=cls.post)

        cls.post_second = Post.objects.create(text='Вторая про панду',
                                              author=cls.user,
                                              group=cls.group)

        cls.post_wrong = Post.objects.create(text='Панда про медведя',
                                             author=cls.user,
                                             group=cls.group_wrong)

        cls.site1 = Site(pk=1,
                         domain='example.com',
                         name='example.com')
        cls.site1.save()

        cls.about_author = FlatPage.objects.create(url='/about-author/',
                                                   title='Об авторе',
                                                   content='Автор это я')

        cls.about_spec = FlatPage.objects.create(url='/about-spec/',
                                                 title='О технологиях',
                                                 content='Джанга')
        cls.about_author.sites.add(cls.site1)
        cls.about_spec.sites.add(cls.site1)
        cls.about_spec.save()
        cls.about_author.save()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts', kwargs={'slug': 'pandas'}),
            'new_post.html': reverse('new_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_maintain_expected_context(self):
        page_database = {
            reverse('index'): [
                {
                    'expected_value': Post.objects.all()[:10],
                    'attribute': 'page'
                },
            ],
            reverse('group_posts', kwargs={'slug': self.group.slug}): [
                {
                    'expected_value': self.group.posts.all()[:10],
                    'attribute': 'page',
                },
                {
                    'expected_value': self.group,
                    'attribute': 'group',
                },
            ],
            reverse('profile', kwargs={'username': self.user.username}): [
                {
                    'expected_value': self.user.posts.all()[:10],
                    'attribute': 'page',
                },
                {
                    'expected_value': self.user,
                    'attribute': 'author',
                },
                {
                    'expected_value': False,
                    'attribute': 'following',
                },
            ],
            reverse('follow_index'): [
                {
                    'expected_value': Post.objects.filter(
                        author__following__user=self.user).all(),
                    'attribute': 'page',
                },
            ],
            reverse('post', kwargs={'username': self.user.username,
                                    'post_id': self.post.pk}): [
                {
                    'expected_value': self.post,
                    'attribute': 'post',
                },
                {
                    'expected_value': self.user,
                    'attribute': 'author',
                },
                {
                    'expected_value': self.post.comments.all(),
                    'attribute': 'comments',
                },
            ]
        }
        for page_url, test_scenarios in page_database.items():
            response = self.authorized_client.get(page_url)
            for scenario in test_scenarios:
                attribute = scenario['attribute']
                with self.subTest(value=page_url):
                    if attribute == 'page':
                        expected_value = tuple(scenario['expected_value'])
                        actual_value = tuple(
                            response.context.get(attribute).object_list)
                    elif isinstance(scenario['expected_value'], QuerySet):
                        expected_value = tuple(scenario['expected_value'])
                        actual_value = tuple(response.context.get(attribute))
                    else:
                        actual_value = response.context.get(attribute)
                        expected_value = scenario['expected_value']
                    self.assertEqual(actual_value, expected_value)

    def test_forms_maintain_correct_data(self):
        form_database = {
            reverse('new_post'): {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            },
            reverse('post_edit', kwargs={'username': self.user.username,
                                         'post_id': self.post.pk}): {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            },
            reverse('post', kwargs={'username': self.user,
                                    'post_id': self.post.pk}): {
                'text': forms.fields.CharField
            },
        }
        for form_url, form_data in form_database.items():
            with self.subTest(value=form_url):
                response = self.authorized_client.get(form_url)
                actual_form = response.context.get('form')
                for field, expected_value in form_data.items():
                    actual_value = actual_form.fields.get(field)
                    self.assertIsInstance(actual_value, expected_value)

    def test_post_appears_in_expected_pages(self):
        post_database = {
            self.post: [
                {
                    'url': reverse('index'),
                    'attribute': 'page',
                    'expected_value': True,
                },
                {
                    'url': reverse('group_posts',
                                   kwargs={'slug': self.post.group.slug}),
                    'attribute': 'page',
                    'expected_value': True,
                },
                {
                    'url': reverse('group_posts',
                                   kwargs={'slug': self.group_wrong.slug}),
                    'attribute': 'page',
                    'expected_value': False,
                },
                {
                    'url': reverse('profile',
                                   kwargs={'username': self.user.username}),
                    'attribute': 'page',
                    'expected_value': True,
                },
                {
                    'url': reverse('profile',
                                   kwargs={'username': self.user_wrong.username}),
                    'attribute': 'page',
                    'expected_value': False,
                },
                {
                    'url': reverse('post',
                                   kwargs={'username':  self.user.username,
                                           'post_id': self.post.pk}),
                    'attribute': 'post',
                    'expected_value': True,
                },
                {
                    'url': reverse('post',
                                   kwargs={'username': self.user.username,
                                           'post_id': self.post_wrong.pk}),
                    'attribute': 'post',
                    'expected_value': False,
                },
            ]
        }

        for post, test_scenarios in post_database.items():
            for scenario in test_scenarios:
                page_url = scenario['url']
                attribute = scenario['attribute']
                expected_value = scenario['expected_value']
                with self.subTest(value=(page_url, post)):
                    response = self.authorized_client.get(page_url)
                    if attribute == 'page':
                        actual_value = post in response.context.get(
                            'page').object_list
                    else:
                        actual_value = post == response.context.get(attribute)
                    self.assertEqual(actual_value, expected_value)

    def test_paginators(self):
        paginator_database = {
            reverse('index'): 10,
            reverse('index') + '?page=2': Post.objects.count() - 10,
            reverse('profile',
                    kwargs={'username': self.user.username}): 10,
            reverse('profile',
                    kwargs={'username': self.user.username,
                            }) + '?page=2': self.user.posts.count() - 10
        }
        for page_url, expected_value in paginator_database.items():
            with self.subTest(value=page_url):
                response = self.authorized_client.get(page_url)
                actual_value = len(response.context.get('page').object_list)
                self.assertEqual(actual_value, expected_value)

    def test_cache(self):
        response = self.authorized_client.get(reverse('index'))
        init_content = response.content
        dummy_post = Post.objects.create(author=self.user,
                                         text='dummy')
        response = self.authorized_client.get(reverse('index'))
        cached_init_content = response.content
        self.assertEqual(init_content, cached_init_content)

        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        updated_post_content = response.content
        self.assertNotEqual(updated_post_content, cached_init_content)

        dummy_post.delete()
        response = self.authorized_client.get(reverse('index'))
        cached_post_content = response.content
        self.assertEqual(cached_post_content, updated_post_content)

        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        refreshed_content = response.content
        self.assertEqual(refreshed_content, init_content)

    def test_user_may_follow_new(self):
        current_subscriptions = User.objects.filter(following__user=self.user)
        expected_value = False
        actual_value = self.user_wrong in current_subscriptions
        self.assertEqual(actual_value, expected_value)
        subscribe_url = reverse('profile_follow',
                                kwargs={'username': self.user_wrong.username})
        self.authorized_client.get(subscribe_url)
        new_subscriptions = User.objects.filter(following__user=self.user)
        expected_value = True
        actual_value = self.user_wrong in new_subscriptions
        self.assertEqual(actual_value, expected_value)

    def test_user_may_unfollow_existent(self):
        current_subscriptions = User.objects.filter(following__user=self.user)
        expected_value = True
        actual_value = self.user_following in current_subscriptions
        self.assertEqual(actual_value, expected_value)
        subscribe_url = reverse('profile_unfollow',
                                kwargs={'username': self.user_following.username})
        self.authorized_client.get(subscribe_url)
        new_subscriptions = User.objects.filter(following__user=self.user)
        expected_value = False
        actual_value = self.user_wrong in new_subscriptions
        self.assertEqual(actual_value, expected_value)


