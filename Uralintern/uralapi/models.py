import os

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator, FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .functions import _upload_to


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='TRAINEE'):
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
    social_url = models.URLField(max_length=200, blank=True, null=True, verbose_name="Личная страница")
    is_active = models.BooleanField(default=True, verbose_name="Активный пользователь")
    is_staff = models.BooleanField(default=False, verbose_name="Сотрудник")
    ROLES = (
        ('ADMIN', 'Администратор'),
        ('CURATOR', 'Куратор'),
        ('EXPERT', 'Эксперт'),
        ('TRAINEE', 'Стажер')
    )
    system_role = models.CharField(max_length=50, choices=ROLES, default="TRAINEE", verbose_name="Роль пользователя")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = UserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.system_role == 'ADMIN':
            self.is_staff = True
            self.is_superuser = True
        super(User, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.unhashed_password = raw_password
        self._password = raw_password

    @property
    def token(self):
        return self._generate_jwt_token()

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def _generate_jwt_token(self):
        dt = datetime.now() + timedelta(days=30)

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
    course = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Курс",
                                              validators=[MinValueValidator(1), MaxValueValidator(6)])
    speciality = models.CharField(max_length=150, blank=True, verbose_name="Специальность")
    institution = models.CharField(max_length=150, blank=True, verbose_name="Учебное заведение")
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Команда")
    image = models.ImageField(upload_to=_upload_to, blank=True, null=True,
                              validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])])
    date_start = models.DateField(auto_created=True, verbose_name="Дата старта")

    def __str__(self):
        return self.user.__str__()

    @property
    def get__image_name(self):
        if self.image:
            return self.image.name.split('/')[1].strip()

    class Meta:
        verbose_name = "Стажер"
        verbose_name_plural = "Стажеры"


class Curator(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="ФИО")

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
    date = models.DateField(verbose_name="Примерная дата начала")
    is_active = models.BooleanField(default=False, verbose_name="Активный этап")

    def __str__(self):
        return self.stage_name

    class Meta:
        verbose_name = "Этап"
        verbose_name_plural = "Этапы"

    def clean(self):
        if not self.event.is_active and self.is_active:
            raise ValidationError("Невозможно активировать этап, мероприятие не активно")


class Event(models.Model):
    event_name = models.CharField(max_length=150, verbose_name="Название мероприятия", unique=True)
    date = models.DateField(verbose_name="Примерная дата начала")
    is_active = models.BooleanField(default=False, verbose_name="Активное мероприятие")

    def __str__(self):
        return self.event_name

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def save(self, *args, **kwargs):
        super(Event, self).save(*args, **kwargs)
        if not self.is_active:
            Stage.objects.filter(event=self.pk).update(is_active=False)

#TODO сделать ссылку на команду назад
class Grade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Имя оценщика")
    trainee = models.ForeignKey('Trainee', on_delete=models.CASCADE, verbose_name="Имя оцениваемого")
    team = models.ForeignKey('Team', on_delete=models.CASCADE, verbose_name="Команда", null=True, blank=True)
    stage = models.ForeignKey('Stage', on_delete=models.CASCADE, verbose_name="Этап")
    competence1 = models.SmallIntegerField(blank=True, null=True, verbose_name="Вовлеченность",
                                           validators=[MinValueValidator(-1), MaxValueValidator(2)])
    competence2 = models.SmallIntegerField(blank=True, null=True, verbose_name="Организованность",
                                           validators=[MinValueValidator(-1), MaxValueValidator(2)])
    competence3 = models.SmallIntegerField(blank=True, null=True, verbose_name="Обучаемость",
                                           validators=[MinValueValidator(-1), MaxValueValidator(2)])
    competence4 = models.SmallIntegerField(blank=True, null=True, verbose_name="Командность",
                                           validators=[MinValueValidator(-1), MaxValueValidator(2)])
    date = models.DateTimeField(auto_created=True, auto_now_add=True, verbose_name="Дата оценки")

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        unique_together = ("user", "trainee", "stage")

    def save(self, *args, **kwargs):
        self.team = self.trainee.team# do whatever processing you want
        super(Grade, self).save(*args, **kwargs)


class GradeDescription(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Описание"
        verbose_name_plural = "Описания оценки"


@receiver(post_save, sender=User)
def create_profiles(sender, instance: User, created, **kwargs):
    if created:
        role = instance.system_role
        if role == "CURATOR":
            Curator.objects.create(user=instance)
        elif role == "TRAINEE":
            Trainee.objects.create(user=instance, date_start=datetime.now())


def delete_parent(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()

post_delete.connect(delete_parent, sender=Trainee)
post_delete.connect(delete_parent, sender=Curator)
post_delete.connect(delete_parent, sender=Expert)