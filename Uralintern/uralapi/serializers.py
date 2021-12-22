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

        # Django предоставляет флаг is_active для модели User. Его цель
        # сообщить, был ли пользователь деактивирован или заблокирован.
        # Проверить стоит, вызвать исключение в случае True.
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
    """ Ощуществляет сериализацию и десериализацию объектов User. """

    # Пароль должен содержать от 8 до 128 символов. Это стандартное правило. Мы
    # могли бы переопределить это по-своему, но это создаст лишнюю работу для
    # нас, не добавляя реальных преимуществ, потому оставим все как есть.
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'system_role', 'password', 'token',)

        # Параметр read_only_fields является альтернативой явному указанию поля
        # с помощью read_only = True, как мы это делали для пароля выше.
        # Причина, по которой мы хотим использовать здесь 'read_only_fields'
        # состоит в том, что нам не нужно ничего указывать о поле. В поле
        # пароля требуются свойства min_length и max_length,
        # но это не относится к полю токена.
        read_only_fields = fields


class UserNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'social_url')
        read_only_fields = fields


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = "__all__"


class CuratorSerializer(serializers.Serializer):
    user = UserNameSerializer()

    class Meta:
        model = Curator
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    curator = CuratorSerializer()

    class Meta:
        model = Team
        fields = ('team_name', 'curator')
        read_only_fields = fields

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

class TraineeSerializer(serializers.ModelSerializer):
    user = UserNameSerializer()
    team = TeamSerializer()
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


# TODO валидировать наличие изображения
class TraineeImageSerializer(serializers.Serializer):
    image = serializers.ImageField(use_url=True, validators=[FileExtensionValidator(['png', 'jpg', 'jpeg'])])

    def update(self, instance: Trainee, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class TraineeTeamSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = UserNameSerializer()
    team = TeamSerializer(required=True)
    internship = serializers.CharField(max_length=100, allow_blank=True)
    image = serializers.ImageField(use_url=True)

    class Meta:
        read_only_fields = ('id', 'user', 'team', 'internship', 'image')


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
        instance.competence1 = validated_data.get('competence1', instance.competence1)
        instance.competence2 = validated_data.get('competence2', instance.competence2)
        instance.competence3 = validated_data.get('competence3', instance.competence3)
        instance.competence4 = validated_data.get('competence4', instance.competence4)
        instance.date = datetime.now()
        # competence_fields = [x for x in validated_data.keys() if 'competence' in x]
        # [setattr(instance, x, validated_data[x]) for x in competence_fields]
        instance.save()
        return instance

    def validate(self, grade):
        if 'trainee' not in grade.keys():
            raise ValidationError('Обязательлное поле trainee')
        if 'stage' not in grade.keys():
            raise ValidationError('Обязательлное поле stage')

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
