from django.urls import path
from .views import (
    LoginAPIView, UserRetrieveAPIView, ListTeamMembersAPIView, ListGradeAPIView, ListStageAPIView,
    UpdateCreateGradeAPIView, TraineeRetriveAPIView, TraineeImageUploadAPIView
)

urlpatterns = [
    path('stage', ListStageAPIView.as_view()),
    path('grade/get', ListGradeAPIView.as_view()),
    path('grade/create-update', UpdateCreateGradeAPIView.as_view()),
    path('trainee/team', ListTeamMembersAPIView.as_view()),
    path('trainee/image-upload', TraineeImageUploadAPIView.as_view()),
    path('trainee', TraineeRetriveAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('user/login', LoginAPIView.as_view()),
]