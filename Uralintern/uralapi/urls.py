from django.urls import path
from .views import (LoginAPIView, UserRetrieveUpdateAPIView)

urlpatterns = [
    path('user', UserRetrieveUpdateAPIView.as_view()),
    path('users/login/', LoginAPIView.as_view()),
]