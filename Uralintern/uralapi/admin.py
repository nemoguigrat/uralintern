import csv
import random
import string
import codecs

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, Group
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.db import transaction
from .models import *
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

admin.site.unregister(Group)


def _generate_password():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    return ''.join(random.choice(chars) for x in range(size))


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


class UserCreationForm(forms.ModelForm):
    is_random_password = forms.BooleanField(label='Случайный пароль')

    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = "__all__"

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают!")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        if self.cleaned_data['is_random_password']:
            user.set_password(_generate_password())
        else:
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm

    fieldsets = (
        (None, {'fields': ('username', 'email', 'system_role', 'password', 'social_url',)}),
        (('Permissions'), {
            'fields': ('is_active', 'is_superuser', 'is_staff'),
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'system_role', 'password1', 'password2', 'is_random_password'),
        }),
    )
    list_display = ('username', 'email', 'system_role', 'is_staff', 'unhashed_password', 'social_url')
    list_filter = ('is_staff', 'is_active',)
    search_fields = ('username',)


@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin, ExportCsvMixin):
    change_list_template = "admin/uralapi/trainee_changelist.html"
    list_display = ('user', 'image', 'course', 'internship', 'speciality', 'team', 'role', 'date_start')
    search_fields = ('user__username', 'course', 'internship', 'speciality', 'team__team_name', 'role',)
    readonly_fields = ('user',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def has_add_permission(self, request):
        return False

    # TODO Отловить ошибки при создании объектов
    def import_csv(self, request):
        if request.method == "POST":
            dialect = csv.Sniffer().sniff(str(request.FILES['csv_file'].readline().decode('utf-8-sig')),
                                          delimiters=',;')
            csv_file = csv.DictReader(codecs.iterdecode(request.FILES['csv_file'], encoding='utf-8-sig'),
                                      dialect=dialect)
            all_data = []
            for row in csv_file:
                all_data.append(row)
            self._create_trainee_user(all_data, request)
            self.message_user(request, "Файл был импортирован")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/uralapi/csv_form.html", payload
        )

    def _create_trainee_user(self, all_data, request):
        local_users = []
        local_trainees = []
        user_create = 0
        user_count = len(all_data)
        for data in all_data:
            if "e-mail" not in data.keys() or "ФИО" not in data.keys():
                all_data.remove(data)
                continue
            random_password = _generate_password()

            user = User(username=data["ФИО"], email=data["e-mail"])  # , social_url=data["Связь"]
            user.set_password(random_password)
            user_create += 1
            self.message_user(request, f"Созданно {user_create} из {user_count}")

            local_users.append(user)

        with transaction.atomic():
            users = User.objects.bulk_create(local_users, ignore_conflicts=True)
        user_to_create = len(users)
        users = User.objects.order_by("-pk")[:user_to_create]
        teams = Team.objects.all()
        cash = list(teams)
        for user, data in zip(users, all_data):
            team = teams.filter(team_name=data["Команда"]).first()
            trainee = Trainee(user=user,
                              internship=data["Направление стажировки"],
                              course=int(data["Курс"]),
                              speciality=data["Учебная специальность"],
                              institution=data["Учебное заведение"],
                              role=data["Роль"],
                              team=team,
                              date_start="-".join(list(data["дата старта"].split(".")[::-1])))
            local_trainees.append(trainee)
        with transaction.atomic():
            Trainee.objects.bulk_create(local_trainees, ignore_conflicts=True)  # ignore_conflict=True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'curator')


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('stage_name', 'date', 'is_active')


@admin.register(Curator)
class CuratorAdmin(admin.ModelAdmin):
    list_display = ('user',)
    readonly_fields = ('user',)

    def has_add_permission(self, request):
        return False


@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = ('user',)
    readonly_fields = ('user',)

    def has_add_permission(self, request):
        return False


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Grade._meta.get_fields() if field.name != 'id']
    search_fields = ('user__username', 'trainee__user__username', 'stage__stage_name')

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "trainee":
    #
    #         kwargs["queryset"] = Trainee.objects.filter(user=request.user)
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('user', 'trainee', 'stage', 'team')
        else:
            return ('team',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'date', 'is_active')


@admin.register(GradeDescription)
class GradeDescriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
