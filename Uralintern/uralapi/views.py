import jwt

from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer

from .models import *
from .renderers import UserJSONRenderer
from .serializers import (
    LoginSerializer, UserSerializer, TraineeTeamSerializer, GradeSerializer, StageSerializer
)


# Create your views here.

class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request):
        user = request.data.get('user', {})

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRetrieveAPIView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)


class StageAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = StageSerializer

    def get(self, request, *args, **kwargs):
        stages = Stage.objects.all()
        serializer = self.serializer_class(stages, many=True)
        return Response({'stages' : serializer.data})


class TeamMembersAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = TraineeTeamSerializer

    def get(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        current_trainee = Trainee.objects.get(user__pk=user_id)
        trainee_team = current_trainee.team
        trainee_team_members = Trainee.objects.filter(team=trainee_team).exclude(user__pk=user_id)

        serializer = self.serializer_class(trainee_team_members, many=True)

        data = []
        for trainee in serializer.data:
            trainee_dict = {}
            trainee_dict['id'] = trainee['id']
            trainee_dict['username'] = trainee['user']['username']
            trainee_dict['team'] = trainee['team']['team_name']
            trainee_dict['role'] = trainee['role']
            data.append(trainee_dict)

        return Response({"trainee": current_trainee.pk, "team": data})


class CreateGradeAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    serializer_class = GradeSerializer

    def get(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None).split()[1]
        user_id = jwt.decode(user_token, settings.SECRET_KEY, algorithms='HS256')['id']

        grades = Grade.objects.filter(user=user_id)
        serializer = self.serializer_class(grades, many=True)
        return Response({"grades": serializer.data})

    def post(self, request, *args, **kwargs):
        pass
