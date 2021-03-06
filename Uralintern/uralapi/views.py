from rest_framework import status
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import MultiPartParser, FileUploadParser, FormParser
from .models import *
from .renderers import UserJSONRenderer
from .serializers import *
from rest_framework import exceptions
from .functions import get_rating, serialize_stages


class LoginAPIView(APIView):
    """Авторизация"""
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class UserRetrieveAPIView(RetrieveAPIView):
    """Информация о пользователе"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserTokenSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TraineeRetrieveAPIView(RetrieveAPIView):
    """Информация о стажере"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeSerializer

    def retrieve(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')
        trainee = Trainee.objects.get(user=request.user)
        serializer = self.serializer_class(trainee)
        return Response({"trainee": serializer.data}, status=status.HTTP_200_OK)


class TraineeImageUploadAPIView(UpdateAPIView):
    """Загрузка изображения"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeImageSerializer
    parser_classes = (MultiPartParser, FormParser, FileUploadParser)

    def patch(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')
        trainee = Trainee.objects.get(user=request.user)
        serializer = self.serializer_class(trainee, data={'image': request.data.get('image', None)})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"image": serializer.validated_data}, status=status.HTTP_200_OK)


class ListStagesAPIView(ListAPIView):
    """Активные этапы мероприятия"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = StageSerializer

    def get(self, request, *args, **kwargs):
        # self.kwargs.get('pk') - id мероприятия указывается в url зарпосе
        stages = Stage.objects.filter(event=self.kwargs.get('pk'), is_active=True)
        serializer = self.serializer_class(stages, many=True)
        return Response({'stages': serializer.data}, status=status.HTTP_200_OK)


class ListTeamMembersAPIView(ListAPIView):
    """Участики команды, в которой состоит стажер и краткая информация об этом стажере"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeTeamSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')
        current_trainee = Trainee.objects.select_related('user', 'team', 'event').get(user=request.user)
        all_stages = Stage.objects.select_related('event').all() # получаем все этапы, что бы закэшировать и использовать потом
        trainee_team = current_trainee.team
        # если стажер не состоит в команде, то поле team будте иметь null
        data = None
        cash = list(all_stages)

        if trainee_team:
            trainee_team_members = Trainee.objects.select_related('user', 'team', 'event').filter(
                team__pk=trainee_team.pk).exclude(
                pk=current_trainee.pk)

            serializer = self.serializer_class(trainee_team_members, many=True)
            data = []
            for trainee in serializer.data:
                # собираем пользовательскую информацию в более удобном виде
                trainee_dict = {}
                trainee_dict['id'] = trainee['id']
                trainee_dict['username'] = trainee['user']['username']
                trainee_dict['team_name'] = trainee['team']['team_name']
                trainee_dict['internship'] = trainee['internship']
                trainee_dict['image'] = trainee['image']
                trainee_dict['social_url'] = trainee['user']['social_url']
                trainee_dict['event'] = trainee['event']['id'] if trainee['event'] else None
                trainee_dict['stages'] = serialize_stages(
                    all_stages.filter(event=trainee['event']['id'], is_active=True)) \
                    if trainee['event'] else []
                data.append(trainee_dict)
        return Response({"trainee":
                             {"id": current_trainee.pk,
                              "username": current_trainee.user.username,
                              "internship": current_trainee.internship,
                              "image": current_trainee.image.url if current_trainee.image else None,
                              "event": current_trainee.event.id if current_trainee.event else None,
                              "stages": serialize_stages(
                                  all_stages.filter(event=current_trainee.event.id, is_active=True)) \
                                  if current_trainee.event else []},
                         "team": data}, status=status.HTTP_200_OK)


class ListTeamMembersForExpertAPIView(ListAPIView):
    """Участики команды для эксертов, кураторов и администраторов"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeTeamSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        # team_members зависит от роли пользователя, если Curator, то отобразятся команды, которые он курирует, если
        # Если админ или эксперт, то все команды
        teams_members = None
        role = request.user.system_role

        if role == 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является экспертом!')
        elif role == 'CURATOR':
            curator = Curator.objects.select_related('user').get(user=request.user)
            teams_members = Trainee.objects.select_related('user', 'team').filter(team__curator=curator).order_by(
                'team__team_name')
        else:
            teams_members = Trainee.objects.select_related('user', 'team').all().order_by('team__team_name')

        all_stages = Stage.objects.select_related('event').all() # получаем все этапы, что бы закэшировать и использовать потом
        serializer = self.serializer_class(teams_members, many=True)
        cash = list(all_stages) # запрос кэшируется
        data = {}
        for trainee in serializer.data:
            trainee_dict = {}
            trainee_dict['id'] = trainee['id']
            trainee_dict['username'] = trainee['user']['username']
            # если стажер не состоит в команде, то по умолчанию его закинет в поле "Без команды"
            trainee_dict['team_name'] = trainee['team']['team_name'] if trainee['team'] else 'Без команды'
            trainee_dict['internship'] = trainee['internship']
            trainee_dict['image'] = trainee['image']
            trainee_dict['social_url'] = trainee['user']['social_url']
            trainee_dict['event'] = trainee['event']['id'] if trainee['event'] else None
            trainee_dict['stages'] = serialize_stages(all_stages.filter(event=trainee['event']['id'], is_active=True)) \
                if trainee['event'] else []

            # если команда еще не в словаре, то создаст, если уже там, то добавит
            if trainee_dict['team_name'] not in data.keys():
                data[trainee_dict['team_name']] = [trainee_dict]
            else:
                data[trainee_dict['team_name']].append(trainee_dict)

        return Response({"teams": data}, status=status.HTTP_200_OK)


class ListGradeToTraineeAPIView(ListAPIView):
    """Оценки, которые получил стажеру"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = ListGradeSerializer

    def get(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')
        grades = Grade.objects.filter(trainee__user=request.user)
        serializer = self.serializer_class(grades, many=True)
        return Response({"grades": serializer.data}, status=status.HTTP_200_OK)


class ListGradeFromTraineeAPIView(ListAPIView):
    """Оценки, которые поставил стажер"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = ListGradeSerializer

    def get(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')
        grades = Grade.objects.filter(user=request.user)
        serializer = self.serializer_class(grades, many=True)
        return Response({"grades": serializer.data}, status=status.HTTP_200_OK)


class UpdateCreateGradeAPIView(APIView):
    """Создаст или обновит существующую оценку"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = UpdateGradeSerializer

    def post(self, request, *args, **kwargs):
        grade = request.data.get('grade', {})
        grade['user'] = request.user.id
        # пробуем получить оценку, если есть, то обновить существующую, если None, то создать новую
        instance_grade = Grade.objects.select_related('user', 'trainee', 'stage') \
            .filter(user=grade['user'], trainee=grade['trainee'], stage=grade['stage']).first()
        # операция обновления стоит дороже
        serializer = self.serializer_class(instance_grade, data=grade) if instance_grade else \
            self.serializer_class(data=grade)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class ReportAPIView(RetrieveAPIView):
    """Сформировать отчет"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def retrieve(self, request, *args, **kwargs):
        if request.user.system_role != 'TRAINEE':
            raise exceptions.PermissionDenied('Пользователь не является стажером!')

        trainee = Trainee.objects.select_related('team').get(user=request.user)
        grades_query = Grade.objects.select_related('user').filter(trainee=trainee) # оценки стажера
        cash = list(grades_query) # кэшируем запрос

        self_rating_query = grades_query.filter(user=request.user) # самооценка
        team_rating_query = grades_query.filter(team=trainee.team) # оценки от команды
        expert_rating_query = grades_query.exclude(user__system_role="TRAINEE") # оценки от админа, куратора, экспертов

        general_rating = get_rating(cash)
        self_rating = get_rating(self_rating_query)
        team_rating = get_rating(team_rating_query)
        expert_rating = get_rating(expert_rating_query)

        return Response({"rating": {
            "general": general_rating,
            "self": self_rating,
            "team": team_rating,
            "expert": expert_rating
        }}, status=status.HTTP_200_OK)


class GradeDescriptionAPIView(ListAPIView):
    """Описание к выставляемым баллам"""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = GradeDescriptionSerializer

    def get(self, request, *args, **kwargs):
        descriptions = GradeDescription.objects.all()
        serializer = self.serializer_class(descriptions, many=True)
        return Response({"descriptions": serializer.data}, status=status.HTTP_200_OK)
