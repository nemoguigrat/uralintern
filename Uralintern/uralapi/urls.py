from django.urls import path
from .views import *
from .models import Stage

urlpatterns = [
    path('stages/<int:pk>', ListStagesAPIView.as_view()),
    path('grade/description', GradeDescriptionAPIView.as_view()),
    path('grade/get/to', ListGradeToTraineeAPIView.as_view()),
    path('grade/get/from', ListGradeFromTraineeAPIView.as_view()),
    path('grade/get/report', ReportAPIView.as_view()),
    path('grade/create-update', UpdateCreateGradeAPIView.as_view()),
    path('trainee/team', ListTeamMembersAPIView.as_view()),
    path('trainee/image-upload', TraineeImageUploadAPIView.as_view()),
    path('trainee', TraineeRetrieveAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('user/login', LoginAPIView.as_view()),
    path('curator/teams', ListTeamMembersForCuratorAPIView.as_view())
]