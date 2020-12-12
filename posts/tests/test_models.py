from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


class PostModelTest(TestCase):

    def __attribute_test(self, model, attribute, expected_database):
        for parameter, expected_value in expected_database.items():
            with self.subTest(value=parameter):
                field = model._meta.get_field(parameter)
                actual_value = field.__getattribute__(attribute)
                self.assertEqual(actual_value, expected_value)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_dummy_text = '01234567890123456789'
        cls.group_dummy_title = 'test_title'
        cls.user = get_user_model().objects.create_user(username='test_name',
                                                        password='test_pwd',
                                                        email='test@yatube.ru')

        cls.group = Group.objects.create(title=cls.group_dummy_title,
                                         slug='test_slug',
                                         description='description of test group')

        cls.post = Post.objects.create(author=cls.user,
                                       text=cls.post_dummy_text,
                                       group=cls.group)

    def test_verbose_name(self):
        verbose_name_database = {
            'Post_verbose_names': {
                'text': 'Текст публикации',
                'pub_date': 'Дата публикации',
                'author': 'Автор'
            },
            'Group_verbose_names': {
                'title': 'Название группы',
                'slug': 'Slug группы',
                'description': 'Описание группы'
            }
        }
        self.__attribute_test(self.post, 'verbose_name',
                              verbose_name_database['Post_verbose_names'])
        self.__attribute_test(self.post.group, 'verbose_name',
                              verbose_name_database['Group_verbose_names'])

    def test_help_name(self):
        help_database = {
            'text': 'Введите текст публикации',
            'group': 'Добавьте группу если хотите, '
                     'но вообще это не обязательно!',
        }
        self.__attribute_test(self.post, 'help_text', help_database)

    def test_post_str(self):
        expected_value = self.post_dummy_text[:15]
        actual_value = self.post.__str__()
        self.assertEqual(actual_value, expected_value)

    def test_group_str(self):
        expected_value = self.group_dummy_title
        actual_value = self.post.group.__str__()
        self.assertEqual(actual_value, expected_value)
