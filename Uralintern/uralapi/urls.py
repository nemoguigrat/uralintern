from django.urls import path
from .views import *
from .models import Stage

urlpatterns = [
    path('stages/<int:pk>', ListStagesAPIView.as_view()), # вывод активных этапов, которые привязаны к мероприятию
    path('grade/description', GradeDescriptionAPIView.as_view()), # описание к выставляемому баллу
    path('grade/get/to', ListGradeToTraineeAPIView.as_view()),# оцеки, которые выствили стажеру
    path('grade/get/from', ListGradeFromTraineeAPIView.as_view()),# оцеки, которые выствил стажер
    path('grade/get/report', ReportAPIView.as_view()),# получить общие баллы
    path('grade/create-update', UpdateCreateGradeAPIView.as_view()),# выствить оценку
    path('trainee/team', ListTeamMembersAPIView.as_view()),# получить состав команды стажера
    path('trainee/image-upload', TraineeImageUploadAPIView.as_view()),# загрузить изображение
    path('trainee', TraineeRetrieveAPIView.as_view()),# информация о стажере
    path('user', UserRetrieveAPIView.as_view()),# информация о пользователе
    path('user/login', LoginAPIView.as_view()),# авторизиция
    # состав команд, к которым привязан куратор, если это админ или эксперт, то составы всех команд
    path('expert/teams', ListTeamMembersForExpertAPIView.as_view())
]