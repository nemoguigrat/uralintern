import csv
import random
import string

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.db import transaction
from .models import *


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'system_role', 'password')}),
        (('Permissions'), {
            'fields': ('is_active', 'is_superuser'),
        }),
        (('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'system_role', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'system_role', 'is_staff', 'unhashed_password')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')


@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin, ExportCsvMixin):
    change_list_template = "admin/uralapi/trainee_changelist.html"
    list_display = ('user', 'image', 'internship', 'speciality', 'team', 'role', 'curator', 'date_start')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    # TODO Отловить ошибки при создании объектов
    def import_csv(self, request):
        if request.method == "POST":
            csv_file = str(request.FILES["csv_file"].read().decode('utf-8-sig')).split('\r\n')
            field_names = csv_file[0].split(",")
            all_data = []
            for row in csv_file[1::]:
                all_data.append(dict(zip(field_names, row.split(","))))
            self._create_trainee_user(all_data)
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/uralapi/csv_form.html", payload
        )

    def _create_trainee_user(self, all_data):
        local_users = []
        local_trainees = []
        user_create = 0
        user_count = len(all_data)
        for data in all_data:
            if "e-mail" not in data.keys() or "ФИО" not in data.keys():
                all_data.remove(data)
                continue
            random_password = self.generate_password()

            user = User(username=data["ФИО"], email=data["e-mail"])
            user.set_password(random_password)
            user_create += 1
            print(f"Созданно {user_create} из {user_count}")

            local_users.append(user)

        with transaction.atomic():
            users = User.objects.bulk_create(local_users)
        user_to_create = len(users)
        users = User.objects.order_by("-pk")[:user_to_create]
        teams = Team.objects.select_related('curator')
        cash = list(teams)
        for user, data in zip(users, all_data):
            team = teams.filter(team_name=data["Команда"]).first()
            curator = team.curator if team != None else None
            trainee = Trainee(user=user,
                              internship=data["Направление стажировки"],
                              course=int(data["Курс"]),
                              speciality=data["Учебная специальность"],
                              institution=data["Учебное заведение"],
                              role=data["Роль"],
                              team=team,
                              curator=curator,
                              date_start="-".join(list(data["дата старта"].split(".")[::-1])))
            local_trainees.append(trainee)
        with transaction.atomic():
            Trainee.objects.bulk_create(local_trainees)

    # TODO изменить алгоритм создания пароля, сохранять и где то сохранять пароли для дальшей рассылки
    def generate_password(self):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        size = random.randint(8, 12)
        return ''.join(random.choice(chars) for x in range(size))


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'curator')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('stage_name', 'date',)


@admin.register(Curator)
class CuratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'vk_url')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Grade._meta.get_fields() if field.name != 'id']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'date',)

@admin.register(GradeDescription)
class GradeDescriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')