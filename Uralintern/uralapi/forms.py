from .models import *
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .functions import generate_password

class CsvImportForm(forms.Form):
    csv_file = forms.FileField(label="Файл в формате CSV UTF-8")


class UserCreationForm(forms.ModelForm):
    is_random_password = forms.BooleanField(label='Случайный пароль', required=False)

    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = "__all__"

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают!")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        # Если is_random_password выбран, то создать случайный пароль
        if self.cleaned_data['is_random_password']:
            user.set_password(generate_password())
        else:
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user