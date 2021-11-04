import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


def upload_to(instance, filename):
    return f'images/{filename}'


# TODO Таблица с критериями оценок

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
    username = models.CharField(db_index=True, max_length=255, verbose_name="ФИО")  # username - ФИО
    email = models.EmailField(db_index=True, unique=True, verbose_name="Почта")
    unhashed_password = models.CharField(max_length=150, verbose_name="Некэшированный пароль", blank=True, null=True)
    is_active = models.BooleanField(default=True, verbose_name="Активный пользователь")
    is_staff = models.BooleanField(default=False)
    ROLES = (
        ('CURATOR', 'Куратор'),
        ('EXPERT', 'Эксперт'),
        ('TRAINEE', 'Стажер')
    )
    system_role = models.CharField(max_length=50, choices=ROLES, default="TRAINEE", verbose_name="Роль пользователя")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
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

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.unhashed_password = raw_password
        self._password = raw_password

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

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Trainee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ФИО")
    internship = models.CharField(max_length=150, blank=True, verbose_name="Напр. стажировки")
    course = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Курс")
    speciality = models.CharField(max_length=150, blank=True, verbose_name="Специальность")
    institution = models.CharField(max_length=150, blank=True, verbose_name="Место обучения")
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Команда")
    role = models.CharField(max_length=100, blank=True, verbose_name="Роль")
    curator = models.ForeignKey('Curator', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Куратор")
    image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    date_start = models.DateField(auto_created=True, verbose_name="Дата старта")

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = "Стажер"
        verbose_name_plural = "Стажеры"


class Curator(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ФИО")
    vk_url = models.URLField(blank=True, null=True, verbose_name="Ссылка в ВК")

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = "Куратор"
        verbose_name_plural = "Кураторы"


class Expert(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ФИО")

    def __str__(self):
        return self.user.__str__()

    class Meta:
        verbose_name = "Эксперт"
        verbose_name_plural = "Эксперты"


class Team(models.Model):
    team_name = models.CharField(max_length=90, verbose_name="Название команды", unique=True)
    curator = models.ForeignKey('Curator', blank=True, null=True, on_delete=models.SET_NULL, verbose_name="Куратор")

    def __str__(self):
        return self.team_name

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"


class Stage(models.Model):
    stage_name = models.CharField(max_length=150, verbose_name="Этап", unique=True)
    event = models.ForeignKey('Event', on_delete=models.CASCADE, verbose_name="Мероприятие")
    date = models.DateField()

    def __str__(self):
        return self.stage_name

    class Meta:
        verbose_name = "Этап"
        verbose_name_plural = "Этапы"


class Event(models.Model):
    event_name = models.CharField(max_length=150, verbose_name="Название мероприятия", unique=True)
    date = models.DateField()

    def __str__(self):
        return self.event_name

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"


class Grade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Имя оценщика")
    trainee = models.ForeignKey('Trainee', on_delete=models.CASCADE, verbose_name="Имя оцениваемого")
    team = models.ForeignKey('Team', on_delete=models.CASCADE, verbose_name="Команда")
    stage = models.ForeignKey('Stage', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Этап")
    competence1 = models.SmallIntegerField(blank=True, null=True, verbose_name="Вовлеченность")
    competence2 = models.SmallIntegerField(blank=True, null=True, verbose_name="Организованность")
    competence3 = models.SmallIntegerField(blank=True, null=True, verbose_name="Обучаемость")
    competence4 = models.SmallIntegerField(blank=True, null=True, verbose_name="Командность")
    date = models.DateTimeField(auto_created=True, auto_now_add=True)

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        unique_together = ("user", "trainee", "stage")


class GradeDescription(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Описание"
        verbose_name_plural = "Описания оценки"


@receiver(post_save, sender=User)
def create_profiles(sender, instance: User, created, **kwargs):
    if created:
        if instance.system_role == "CURATOR":
            Curator.objects.create(user=instance)
        elif instance.system_role == "TRAINEE":
            Trainee.objects.create(user=instance, date_start=datetime.now())
