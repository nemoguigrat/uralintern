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
from .serializers import (
    LoginSerializer, UserSerializer, TraineeTeamSerializer, GradeSerializer, StageSerializer, TraineeSerializer,
    TraineeImageSerializer
)


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
        serializer = self.serializer_class(trainee, data={'image' : request.data.get('image', None)})
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
        grade_note = request.data.get('grades', {})[0]

        instance_grade = Grade.objects \
            .filter(user=grade_note['user'], trainee=grade_note['trainee'], stage=grade_note['stage']) \
            .first()
        serializer = self.serializer_class(instance_grade, data=grade_note) if instance_grade else \
            self.serializer_class(data=grade_note)

        serializer.is_valid()
        serializer.save()
        return Response(status=status.HTTP_200_OK)
