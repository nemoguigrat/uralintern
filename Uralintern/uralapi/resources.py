from import_export import fields
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from .models import Grade, Trainee, User, Team, Stage


class GradeResource(ModelResource):
    def get_export_headers(self):
        headers = super().get_export_headers()
        model_verbose = dict([(field.name, field.verbose_name) for field in Grade._meta.get_fields()])
        for index in range(len(headers)):
            if '_' in headers[index]:
                headers[index] = headers[index].split('_')[0]
            if headers[index] in model_verbose.keys():
                headers[index] = model_verbose[headers[index]]
        return headers

    class Meta:
        model = Grade
        fields = ('user__username',
                  'trainee__user__username',
                  'team__team_name',
                  'stage__stage_name',
                  'competence1',
                  'competence2',
                  'competence3',
                  'competence4',
                  'date')
