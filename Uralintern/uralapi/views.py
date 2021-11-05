import jwt

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


# Create your views here.

class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def get(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class TraineeRetrieveAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeSerializer

    def retrieve(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        trainee = Trainee.objects.get(user__pk=user_id)
        serializer = self.serializer_class(trainee)
        return Response({"trainee": serializer.data}, status=status.HTTP_200_OK)

#TODO возможно придется переписать, так как кураторы и эксперты пока так же могут войти в приложение
class TraineeImageUploadAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeImageSerializer
    parser_classes = (MultiPartParser, FormParser, FileUploadParser)

    def patch(self, request, *args, **kwargs):
        print(request.data)
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        trainee = Trainee.objects.get(user__pk=user_id)
        if trainee.image:
            os.remove(settings.MEDIA_ROOT + "/" + trainee.image.name)
        serializer = self.serializer_class(trainee, data={'image': request.data.get('image', None)})
        serializer.is_valid()
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class ListStageAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = StageSerializer

    def get(self, request, *args, **kwargs):
        stages = Stage.objects.all()
        serializer = self.serializer_class(stages, many=True)
        return Response({'stages': serializer.data}, status=status.HTTP_200_OK)


class ListTeamMembersAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeTeamSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        current_trainee = Trainee.objects.get(user__pk=user_id)
        trainee_team = current_trainee.team
        trainee_team_members = Trainee.objects.filter(team=trainee_team).exclude(pk=current_trainee.pk)

        serializer = self.serializer_class(trainee_team_members, many=True)

        data = []
        for trainee in serializer.data:
            print(trainee)
            trainee_dict = {}
            trainee_dict['id'] = trainee['id']
            trainee_dict['username'] = trainee['user']['username']
            trainee_dict['team'] = trainee['team']['team_name']
            trainee_dict['role'] = trainee['role']
            trainee_dict['image'] = trainee['image']
            data.append(trainee_dict)
        return Response({"trainee":
                             {"id": current_trainee.pk,
                              "username": current_trainee.user.username,
                              "image": current_trainee.image.url if current_trainee.image else None},
                         "team": data}, status=status.HTTP_200_OK)


class ListGradeAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = GradeSerializer

    def get(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']
        current_trainee = Trainee.objects.get(user__pk=user_id)
        grades = Grade.objects.filter(trainee=current_trainee)
        serializer = self.serializer_class(grades, many=True)
        return Response({"grades": serializer.data}, status=status.HTTP_200_OK)


class UpdateCreateGradeAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = GradeSerializer

    def post(self, request, *args, **kwargs):
        grade_note = request.data.get('grades', {})

        for grade in grade_note:
            instance_grade = Grade.objects \
                .filter(user=grade['user'], trainee=grade['trainee'], stage=grade['stage']) \
                .first()
            serializer = self.serializer_class(instance_grade, data=grade) if instance_grade else \
                self.serializer_class(data=grade)

            serializer.is_valid()
            serializer.save()
        return Response(status=status.HTTP_200_OK)


class ReportAPIView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)

    def retrieve(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        trainee = Trainee.objects.get(user__pk=user_id)
        grades_query = Grade.objects.select_related('user').filter(trainee=trainee)
        cash = list(grades_query)

        self_rating_query = grades_query.filter(user=user_id)
        team_rating_query = grades_query.filter(team=trainee.team)
        curator_rating_query = grades_query.filter(user__system_role = "CURATOR")
        expert_rating_query = grades_query.filter(user__system_role = "EXPERT")

        general_rating = self._get_rating(cash)
        self_rating = self._get_rating(self_rating_query)
        team_rating = self._get_rating(team_rating_query)
        curator_rating = self._get_rating(curator_rating_query)
        expert_rating = self._get_rating(expert_rating_query)

        return Response({
            "general" : general_rating,
            "self" : self_rating,
            "team" : team_rating,
            "curator" : curator_rating,
            "expert" : expert_rating
        }, status=status.HTTP_200_OK)

    def _get_rating(self, grades):
        rating_list = [[],[],[],[]]
        for grade in grades:
            rating_list[0].append(grade.competence1 if grade.competence1 != None else 0)
            rating_list[1].append(grade.competence2 if grade.competence2 != None else 0)
            rating_list[2].append(grade.competence3 if grade.competence3 != None else 0)
            rating_list[3].append(grade.competence4 if grade.competence4 != None else 0)
        return {"competence1" :self.__average(rating_list[0]),
                "competence2": self.__average(rating_list[1]),
                "competence3": self.__average(rating_list[2]),
                "competence4": self.__average(rating_list[3])}

    def __average(self, grades : list):
        return (sum(grades) / len(grades)) if len(grades) > 0 else 0


class GradeDescriptionAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = GradeDescriptionSerializer

    def get(self, request, *args, **kwargs):
        descriptions = GradeDescription.objects.all()
        serializer = self.serializer_class(descriptions, many=True)
        return Response({"descriptions": serializer.data}, status=status.HTTP_200_OK)
