from django.urls import path
from .views import (LoginAPIView, UserRetrieveAPIView, TeamMembersAPIView)

urlpatterns = [
    path('user-team', TeamMembersAPIView.as_view()),
    path('user', UserRetrieveAPIView.as_view()),
    path('users/login/', LoginAPIView.as_view()),
]