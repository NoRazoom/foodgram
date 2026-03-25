from django.db import models
from django.contrib.auth.models import AbstractUser


EMAIL_MAX_LENGTH = 256
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150


class User(AbstractUser):
    """
    Переопределенная модель пользователя.

    Меняем переменные полей под тз -
    допустимую длину, необходимость.
    """

    email = models.EmailField('email',
                              unique=True,
                              max_length=EMAIL_MAX_LENGTH)
    first_name = models.CharField('Имя',
                                  max_length=FIRST_NAME_MAX_LENGTH,
                                  blank=False)
    last_name = models.CharField('Фамилия',
                                 max_length=LAST_NAME_MAX_LENGTH,
                                 blank=False)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Follow(models.Model):
    """Подписки пользователя на других пользователей"""

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='follower'
    )
    following = models.ManyToManyField(User, related_name='following')
