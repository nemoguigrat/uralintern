from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import *


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    username = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=128, write_only=True)
    system_role = serializers.CharField(max_length=128, read_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        # В методе validate мы убеждаемся, что текущий экземпляр
        # LoginSerializer значение valid. В случае входа пользователя в систему
        # это означает подтверждение того, что присутствуют адрес электронной
        # почты и то, что эта комбинация соответствует одному из пользователей.
        email = data.get('email', None)
        password = data.get('password', None)

        # Вызвать исключение, если не предоставлена почта.
        if email is None:
            raise serializers.ValidationError(
                'An email address is required to log in.'
            )

        # Вызвать исключение, если не предоставлен пароль.
        if password is None:
            raise serializers.ValidationError(
                'A password is required to log in.'
            )

        # Метод authenticate предоставляется Django и выполняет проверку, что
        # предоставленные почта и пароль соответствуют какому-то пользователю в
        # нашей базе данных. Мы передаем email как username, так как в модели
        # пользователя USERNAME_FIELD = email.
        user = authenticate(username=email, password=password)
        # Если пользователь с данными почтой/паролем не найден, то authenticate
        # вернет None. Возбудить исключение в таком случае.
        if user is None:
            raise serializers.ValidationError(
                'A user with this email and password was not found.'
            )

        if not user.is_active:
            raise serializers.ValidationError(
                'This user has been deactivated.'
            )

        # Метод validate должен возвращать словать проверенных данных. Это
        # данные, которые передются в т.ч. в методы create и update.
        return {
            'id': user.pk,
            'email': user.email,
            'username': user.username,
            'system-role': user.system_role,
            'token': user.token
        }


class UserTokenSerializer(serializers.ModelSerializer):
    """
    Сериализует поля 'id', 'email', 'username', 'system_role', 'password', 'token' из модели User
    """

    # Пароль должен содержать от 8 до 128 символов. Это стандартное правило.
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'system_role', 'password', 'token',)

        read_only_fields = fields


class UserNameSerializer(serializers.ModelSerializer):
    """Сериализует поля 'id', 'username', 'social_url' из модели User"""
    class Meta:
        model = User
        fields = ('id', 'username', 'social_url')
        read_only_fields = fields


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = "__all__"


class CuratorSerializer(serializers.Serializer):
    # Использование дугого сериализатора для поля, дает возможноть извлечь информацию в удобном виде из родительской модели
    user = UserNameSerializer()

    class Meta:
        model = Curator
        fields = "__all__"


class TeamForTraineeSerializer(serializers.ModelSerializer):
    """Сериализация информации о команде для авторизованого стажера(содержит информацию о кураторе)"""

    # Использование дугого сериализатора для поля, дает возможноть извлечь информацию в удобном виде из родительской модели
    curator = CuratorSerializer()

    class Meta:
        model = Team
        fields = ('team_name', 'curator')
        read_only_fields = fields

class TeamForTeamMembersSerializer(serializers.ModelSerializer):
    """Сериализация информации о команде для членов команды(содержит только название команды)"""
    class Meta:
        model = Team
        fields = ('team_name',)
        read_only_fields = fields

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

class TraineeSerializer(serializers.ModelSerializer):
    # Использование дугого сериализатора для поля, дает возможноть извлечь информацию в удобном виде из родительской модели
    user = UserNameSerializer()
    team = TeamForTraineeSerializer()
    event = EventSerializer()

    class Meta:
        model = Trainee
        fields = "__all__"
        read_only_fields = ('user',
                            'internship',
                            'course',
                            'speciality',
                            'institution',
                            'team',
                            'image',
                            'event',
                            'date_start')


class TraineeImageSerializer(serializers.Serializer):
    image = serializers.ImageField(use_url=True, validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])])

    def update(self, instance: Trainee, validated_data):
        # Если в словаре есть такой ключ, перепишет данные в базе, либо оствит то, что было
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class TraineeTeamSerializer(serializers.Serializer):
    # Использование дугого сериализатора для поля, дает возможноть извлечь информацию в удобном виде из родительской модели
    id = serializers.IntegerField()
    user = UserNameSerializer()
    team = TeamForTeamMembersSerializer(required=True)
    internship = serializers.CharField(max_length=100, allow_blank=True)
    image = serializers.ImageField(use_url=True)
    event = EventSerializer()

    class Meta:
        read_only_fields = ('id', 'user', 'team', 'internship', 'image', 'event')


class ListGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ('user',
                  'trainee',
                  'team',
                  'stage',
                  'competence1',
                  'competence2',
                  'competence3',
                  'competence4',)
        read_only_fields = fields


class UpdateGradeSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return Grade.objects.create(**validated_data)

    def update(self, instance: Grade, validated_data):
        # Далее, если в словаре есть такой ключ, перепишет данные в базе, либо оствит то, что было
        instance.competence1 = validated_data.get('competence1', instance.competence1)
        instance.competence2 = validated_data.get('competence2', instance.competence2)
        instance.competence3 = validated_data.get('competence3', instance.competence3)
        instance.competence4 = validated_data.get('competence4', instance.competence4)
        instance.date = datetime.now()
        instance.save()
        return instance

    def validate(self, grade):
        if 'trainee' not in grade.keys():
            raise ValidationError('Обязательлное поле trainee')
        if 'stage' not in grade.keys():
            raise ValidationError('Обязательлное поле stage')
        # Проверяет активен ли этап, по которому дают оценку, если нет, то оцнить по нему нельзя, будет брошенно исключение
        if not grade['stage'].is_active:
            raise ValidationError('Невозможно дать оценку по не активному этапу!')

        return grade

    class Meta:
        model = Grade
        fields = ('user',
                  'trainee',
                  'stage',
                  'competence1',
                  'competence2',
                  'competence3',
                  'competence4',)


class GradeDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeDescription
        fields = "__all__"
