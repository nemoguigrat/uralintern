from django.urls import path
from .views import (
    LoginAPIView, UserRetrieveAPIView, ListTeamMembersAPIView, ListGradeAPIView, ListStageAPIView, UpdateCreateGradeAPIView
)

urlpatterns = [
    path('stage', ListStageAPIView.as_view()),
    path('grade/get', ListGradeAPIView.as_view()),
    path('grade/create-update', UpdateCreateGradeAPIView.as_view()),
    path('user/team', ListTeamMembersAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('users/login', LoginAPIView.as_view()),
]