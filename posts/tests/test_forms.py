import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group


class PostCreateFormTests(TestCase):
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
        cls.txt_file = b'dummy_file_content'
        cls.uploaded = SimpleUploadedFile(name='small.gif',
                                          content=cls.small_gif,
                                          content_type='image/gif')

        cls.txt_uploaded = SimpleUploadedFile(name='test.txt',
                                              content=cls.txt_file,
                                              content_type='text/plain')

        cls.user = get_user_model().objects.create_user(username='panda')
        cls.group = Group.objects.create(title='pandas group',
                                         slug='pandas',
                                         description='Pandas stories')
        cls.post = Post.objects.create(text='Оригинальный Текст',
                                       author=cls.user,
                                       group=cls.group)
        cls.update_post_url = reverse('post_edit',
                                      kwargs={'username': cls.user.username,
                                              'post_id': cls.post.pk})
        cls.get_post_url = reverse('post',
                                   kwargs={'username': cls.user.username,
                                           'post_id': cls.post.pk})
        cls.comment_post_url = reverse('add_comment',
                                       kwargs={'username': cls.user.username,
                                               'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        form_data = {
            'group': self.group.id,
            'text': 'absolutely unique post',
        }
        expected_value = Post.objects.count() + 1
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('index'))
        actual_value = Post.objects.count()
        self.assertEqual(expected_value, actual_value)
        post_text_from_bd = Post.objects.filter(text=form_data['text'])[0]
        self.assertEqual(post_text_from_bd.text, form_data['text'])

    def test_image_uploaded_by_post_form(self):
        form_data = {
            'group': self.group.id,
            'text': 'second unique post',
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('index'))
        post_text_from_bd = Post.objects.filter(text=form_data['text'])[0]
        image_path = post_text_from_bd.image.name
        image_name = image_path.split('/')[-1] if image_path else None
        self.assertEqual(image_name, self.uploaded.name)

    def test_txt_file_not_uploaded_by_post_form(self):
        form_data = {
            'group': self.group.id,
            'text': 'third unique post',
            'image': self.txt_uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        expected_error = ['Загрузите правильное изображение. '
                          'Файл, который вы загрузили, '
                          'поврежден или не является изображением.']
        self.assertFormError(response, 'form', 'image', expected_error)

    def test_modify_post(self):
        form_data = {
            'group': self.group.id,
            'text': 'absolutely unique post',
        }
        response = self.authorized_client.post(self.update_post_url,
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, self.get_post_url)
        self.post.refresh_from_db()
        actual_value = self.post.text
        expected_value = form_data['text']
        self.assertEqual(actual_value, expected_value)

    def test_comment_added_through_form(self):
        form_data = {
            'text': 'absolutely tesitng comment',
        }
        response = self.authorized_client.post(self.comment_post_url,
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, self.get_post_url)

        expected_value = form_data['text']
        added_comment = self.post.comments.filter(text=expected_value).all()[0]
        actual_value = added_comment.text
        self.assertEqual(actual_value, expected_value)

    def test_anonymous_can_not_comment(self):
        form_data = {
            'text': 'absolutely useless comment',
        }
        login_url = reverse('login')
        redirect_url = (f'{login_url}'
                        f'?next='
                        f'{self.comment_post_url}')

        response = self.guest_client.post(self.comment_post_url,
                                          data=form_data,
                                          follow=True)

        self.assertRedirects(response, redirect_url)
