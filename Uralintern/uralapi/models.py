import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


# Create your models here.

class UserManager(BaseUserManager):
    """
    Django требует, чтобы кастомные пользователи определяли свой собственный
    класс Manager. Унаследовавшись от BaseUserManager, мы получаем много того
    же самого кода, который Django использовал для создания User (для демонстрации).
    """

    def create_user(self, username, email, password=None, role='TRAINEE'):
        """ Создает и возвращает пользователя с имэйлом, паролем и именем. """
        if username is None:
            raise TypeError('Users must have a username.')
        if len(username.split()) < 2:
            raise TypeError('Username must be user full name')

        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(username=username, email=self.normalize_email(email), system_role=role)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username, email, password):
        """ Создает и возввращет пользователя с привилегиями суперадмина. """
        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.create_user(username, email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)  # username - ФИО
    email = models.EmailField(db_index=True, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    ROLES = (
        ('CURATOR', 'Куратор'),
        ('EXPERT', 'Эксперт'),
        ('TRAINEE', 'Стажер')
    )
    system_role = models.CharField(max_length=50, choices=ROLES, default="TRAINEE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Дополнительный поля, необходимые Django
    # при указании кастомной модели пользователя.
    # Свойство USERNAME_FIELD сообщает нам, какое поле мы будем использовать
    # для входа в систему. В данном случае мы хотим использовать почту.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]
    # Сообщает Django, что определенный выше класс UserManager
    # должен управлять объектами этого типа.
    objects = UserManager()

    def __str__(self):
        """ Строковое представление модели (отображается в консоли) """
        return self.username

    @property
    def token(self):
        """
        Позволяет получить токен пользователя путем вызова user.token, вместо
        user._generate_jwt_token(). Декоратор @property выше делает это
        возможным. token называется "динамическим свойством".
        """
        return self._generate_jwt_token()

    def get_full_name(self):
        """
        Этот метод требуется Django для таких вещей, как обработка электронной
        почты. Обычно это имя фамилия пользователя, но поскольку мы не
        используем их, будем возвращать username.
        """
        return self.username

    def get_short_name(self):
        """ Аналогично методу get_full_name(). """
        return self.username

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=1)

        token = jwt.encode({
            'id': self.pk,
            'exp': dt.utcfromtimestamp(dt.timestamp())  # CHANGE HERE
        }, settings.SECRET_KEY, algorithm='HS256')

        return token


class Trainee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    internship = models.CharField(max_length=150, blank=True)
    course = models.PositiveSmallIntegerField(blank=True, null=True)
    speciality = models.CharField(max_length=150, blank=True)
    institution = models.CharField(max_length=150, blank=True)
    team = models.OneToOneField('Team', on_delete=models.CASCADE, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True)
    curator = models.ForeignKey('Curator', on_delete=models.CASCADE, blank=True, null=True)
    # image = ...
    date_start = models.DateField(auto_created=True)

    def __str__(self):
        return self.user.__str__()


class Curator(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vk_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user.__str__()


class Expert(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.__str__()


class Team(models.Model):
    team_name = models.CharField(max_length=90)
    curator = models.ForeignKey('Curator', on_delete=models.CASCADE)

    def __str__(self):
        return self.team_name


class Stage(models.Model):
    stage_name = models.CharField(max_length=150)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return self.stage_name


class Event(models.Model):
    event_name = models.CharField(max_length=150)
    date = models.DateField()

    def __str__(self):
        return self.event_name


class Grade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trainee = models.ForeignKey('Trainee', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    stage = models.ForeignKey('Stage', on_delete=models.CASCADE)
    competence = models.SmallIntegerField()
    date = models.DateTimeField(auto_created=True)

# TODO временное решение для хранения пароля, заменить
class LoginData(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=20)
    email = models.EmailField(max_length=100)


@receiver(post_save, sender=User)
def create_profiles(sender, instance : User, created, **kwargs):
    if created:
        if instance.system_role == "CURATOR":
            Curator.objects.create(user=instance)
        elif instance.system_role == "TRAINEE":
            Trainee.objects.create(user=instance, date_start=datetime.now())
