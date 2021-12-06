import random
import string


# Генерация пароля во время импорта в TraineeAdmin и при создании пользователя в UserCreationForm
def _generate_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    return ''.join(random.choice(chars) for x in range(size))

def _get_report(trainee, grades):
    general_rating_query = grades.filter(trainee=trainee)
    self_rating_query = grades.filter(user=trainee.user)
    team_rating_query = grades.filter(team=trainee.team)
    expert_rating_query = grades.exclude(user__system_role="TRAINEE")

    general_rating = _get_rating(general_rating_query)
    self_rating = _get_rating(self_rating_query)
    team_rating = _get_rating(team_rating_query)
    expert_rating = _get_rating(expert_rating_query)

    return {
        "general": general_rating,
        "self": self_rating,
        "team": team_rating,
        "expert": expert_rating}


# Подсчет оценок для стажеров в генерации отчета и ReportAPIView
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


# Установка имени для загруженного изображения в Trainee models.py
def _upload_to(instance, filename: str):
    ext = filename.split('.')[-1]
    return f'images/{instance.id}.{ext}'