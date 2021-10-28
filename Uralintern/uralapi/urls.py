from django.urls import path

from .views import LoginAPIView

urlpatterns = [
    path('users/login/', LoginAPIView.as_view()),
]