import random
import string

#Генерация отчетов в ПДФ в TraineeAdmin actions
def _generate_pdf_report(request, queryset):
    pass

#Генерация пароля во время импорта в TraineeAdmin и при создании пользователя в UserCreationForm
def _generate_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    return ''.join(random.choice(chars) for x in range(size))

#Подсчет оценок для стажеров в генерации отчета и ReportAPIView
def _get_rating(grades):
    rating_list = [[], [], [], []]
    average = lambda grades: round(sum(grades) / len(grades), 2) if len(grades) > 0 else 0
    for grade in grades:
        rating_list[0].append(grade.competence1 if grade.competence1 != None else 0)
        rating_list[1].append(grade.competence2 if grade.competence2 != None else 0)
        rating_list[2].append(grade.competence3 if grade.competence3 != None else 0)
        rating_list[3].append(grade.competence4 if grade.competence4 != None else 0)
    return {"competence1": average(rating_list[0]),
            "competence2": average(rating_list[1]),
            "competence3": average(rating_list[2]),
            "competence4": average(rating_list[3])}

#Установка имени для загруженного изображения в Trainee models.py
def _upload_to(instance, filename: str):
    ext = filename.split('.')[-1]
    return f'images/{instance.id}.{ext}'
