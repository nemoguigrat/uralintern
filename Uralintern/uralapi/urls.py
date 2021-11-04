from django.urls import path
from .views import (
    LoginAPIView, UserRetrieveAPIView, ListTeamMembersAPIView, ListGradeAPIView, ListStageAPIView,
    UpdateCreateGradeAPIView, TraineeRetrieveAPIView, TraineeImageUploadAPIView, ReportAPIView,GradeDescriptionAPIView
)

urlpatterns = [
    path('stage', ListStageAPIView.as_view()),
    path('grade/description', GradeDescriptionAPIView.as_view()),
    path('grade/get/all', ListGradeAPIView.as_view()),
    path('grade/get/report', ReportAPIView.as_view()),
    path('grade/create-update', UpdateCreateGradeAPIView.as_view()),
    path('trainee/team', ListTeamMembersAPIView.as_view()),
    path('trainee/image-upload', TraineeImageUploadAPIView.as_view()),
    path('trainee', TraineeRetrieveAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('user/login', LoginAPIView.as_view()),
]