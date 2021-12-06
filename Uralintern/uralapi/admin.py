import csv
import codecs

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, Group
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.db import transaction
from .models import *
from import_export.admin import ExportMixin
from .resources import GradeResource
from django.contrib import messages
from .functions import _generate_password, _get_report
from .forms import CsvImportForm, UserCreationForm

admin.site.unregister(Group)


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
    list_filter = ('is_staff', 'is_active', 'system_role')
    search_fields = ('username',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('system_role',)
        return ()


@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin):
    change_list_template = "admin/uralapi/trainee_changelist.html"
    list_display = ('user', 'image', 'course', 'internship', 'speciality', 'institution', 'team', 'date_start')
    search_fields = ('user__username', 'course', 'internship', 'speciality', 'team__team_name')
    readonly_fields = ('user',)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv),
                 name='%s_%s_import' % self.get_model_info())
        ]
        return my_urls + urls

    def get_model_info(self):
        app_label = self.model._meta.app_label
        return (app_label, self.model._meta.model_name)

    def has_add_permission(self, request):
        return False

    def import_csv(self, request, *args, **kwargs):
        from django.template.response import TemplateResponse

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

        context = {}
        context.update(self.admin_site.each_context(request))

        context['title'] = 'Импорт стажеров'
        context['form'] = form
        context['opts'] = self.model._meta
        request.current_app = self.admin_site.name

        return TemplateResponse(request, ['admin/uralapi/csv_form.html'],
                                context)

    def _create_trainee_user(self, all_data, request):
        local_users = []
        local_trainees = []
        validated_data = []
        for data in all_data:
            if "Частный e-mail" in data.keys() and "ФИО" in data.keys() and data["Частный e-mail"]:
                random_password = _generate_password()

                user = User(username=data["ФИО"], email=data["Частный e-mail"], social_url=data["Личная страница"])
                user.set_password(random_password)

                local_users.append(user)
                validated_data.append(data)

        with transaction.atomic():
            users = User.objects.bulk_create(local_users, ignore_conflicts=True)
        user_to_create = len(users)
        users = User.objects.order_by("-pk")[:user_to_create]
        teams = Team.objects.all()
        cash = list(teams)
        for user, data in zip(users, validated_data[::-1]):
            team = teams.filter(team_name=data["Команда"]).first()
            trainee = Trainee(user=user,
                              internship=data["Направление стажировки"],
                              course=int(data["Курс"]),
                              speciality=data["Учебная специальность"],
                              institution=data["Учебное заведение"],
                              team=team,
                              date_start=datetime.today())
            local_trainees.append(trainee)
        with transaction.atomic():
            Trainee.objects.bulk_create(local_trainees, ignore_conflicts=True)  # ignore_conflict=True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'curator')
    list_editable = ('curator',)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('stage_name', 'date', 'event', 'is_active')
    list_editable = ('date', 'is_active')


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
class GradeAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = GradeResource
    list_display = [field.name for field in Grade._meta.get_fields() if field.name != 'id']
    search_fields = ('user__username', 'trainee__user__username', 'stage__stage_name')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('user', 'trainee', 'stage', 'team')
        else:
            return ('team',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'date', 'is_active')
    list_editable = ('date', 'is_active')


@admin.register(GradeDescription)
class GradeDescriptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
