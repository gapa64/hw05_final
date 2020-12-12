from django.contrib.auth import get_user_model
from django.db.models import Max
from django.test import TestCase, Client
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.models import Site
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='panda')
        cls.user_other = User.objects.create_user(username='bear')
        cls.group = Group.objects.create(title='pandas group',
                                         slug='pandas',
                                         description='Pandas stories')
        cls.post = Post.objects.create(text='История про панду',
                                       author=cls.user,
                                       group=cls.group)

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

        cls.index_url = reverse('index')
        cls.login_url = reverse('login')
        cls.new_post_url = reverse('new_post')
        cls.about_spec_url = reverse('about-spec')
        cls.about_author_url = reverse('about-author')
        cls.group_url = reverse('group_posts',
                                kwargs={'slug': cls.group.slug})
        cls.profile_url = reverse('profile',
                                  kwargs={'username': cls.user.username})
        cls.profile_other_url = reverse(
                                    'profile',
                                    kwargs={
                                        'username': cls.user_other.username
                                    })
        cls.post_url = reverse('post',
                               kwargs={'username': cls.user.username,
                                       'post_id': cls.post.pk})

        cls.post_edit_url = reverse('post_edit',
                                    kwargs={'username': cls.user.username,
                                            'post_id': cls.post.pk})

        cls.login_post_edit_redirect_url = (f'{cls.login_url}'
                                            f'?next='
                                            f'{cls.post_edit_url}')
        cls.login_new_post_redirect_url = (f'{cls.login_url}'
                                           f'?next='
                                           f'{cls.new_post_url}')
        cls.follow_index_url = reverse('follow_index')
        cls.follow_new_url = reverse(
                                'profile_follow',
                                kwargs={
                                    'username': cls.user_other.username
                                })
        cls.unfollow_new_url = reverse(
                                'profile_follow',
                                kwargs={
                                    'username': cls.user_other.username
                                })
        cls.follow_index_redirect_url = (f'{cls.login_url}'
                                         f'?next='
                                         f'{cls.follow_index_url}')

        cls.follow_new_redirect_url = (f'{cls.login_url}'
                                       f'?next='
                                       f'{cls.follow_new_url}')

        cls.unfollow_new_redirect_url = (f'{cls.login_url}'
                                         f'?next='
                                         f'{cls.unfollow_new_url}')

        max_post_pk = cls.user.posts.aggregate(Max("pk"))['pk__max']
        cls.unreacheable_page_url = reverse(
                                        'post',
                                        kwargs={'username': cls.user.username,
                                                'post_id': max_post_pk + 1})

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.other_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_client.force_login(self.user_other)

    def test_page_routing(self):
        default_test = {
            'method': self.assertEqual,
            'expected_value': 200,
        }

        default_scenarios = {
            self.authorized_client: default_test,
            self.guest_client: default_test,
        }

        page_database = {
            self.index_url: default_scenarios,
            self.group_url: default_scenarios,
            self.profile_url: default_scenarios,
            self.post_url: default_scenarios,
            self.about_spec_url: default_scenarios,
            self.about_author_url: default_scenarios,
            self.unreacheable_page_url: {
                self.guest_client: {
                    'method': self.assertEqual,
                    'expected_value': 404
                },
            },
            self.new_post_url: {
                self.authorized_client: default_test,
                self.guest_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.login_new_post_redirect_url
                },
            },
            self.post_edit_url: {
                self.guest_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.login_post_edit_redirect_url,
                },
                self.other_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.post_url,
                },
                self.authorized_client: default_test,
            },
            self.follow_index_url: {
                self.authorized_client: default_test,
                self.guest_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.follow_index_redirect_url,
                },
            },
            self.follow_new_url: {
                self.authorized_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.profile_other_url,
                },
                self.guest_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.follow_new_redirect_url,
                },
            },
            self.unfollow_new_url: {
                self.authorized_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.profile_other_url,
                },
                self.guest_client: {
                    'method': self.assertRedirects,
                    'expected_value': self.unfollow_new_redirect_url,
                },
            },
        }

        for path, scenario_database in page_database.items():
            for client, test_data in scenario_database.items():
                method = test_data['method']
                expected_value = test_data['expected_value']
                with self.subTest(value=path):
                    response = client.get(path)
                    if method == self.assertEqual:
                        actual_value = response.status_code
                    else:
                        actual_value = response
                    method(actual_value, expected_value)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.index_url: 'index.html',
            self.group_url: 'group.html',
            self.new_post_url: 'new_post.html',
            self.profile_url: 'profile.html',
            self.post_url: 'post.html',
            self.post_edit_url: 'new_post.html',
            self.follow_index_url: 'follow.html'
        }
        for path, template in templates_url_names.items():
            with self.subTest(value=path):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(response, template)


