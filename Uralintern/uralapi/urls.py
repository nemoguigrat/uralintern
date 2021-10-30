from django.urls import path
from .views import LoginAPIView, UserRetrieveAPIView, TeamMembersAPIView, CreateGradeAPIView, StageAPIView

urlpatterns = [
    path('stage', StageAPIView.as_view()),
    path('grade', CreateGradeAPIView.as_view()),
    path('user/team', TeamMembersAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('users/login', LoginAPIView.as_view()),
]