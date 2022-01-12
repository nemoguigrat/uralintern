## Uralintern API
### Информация
Актуальная документация к API находится в разделе Wiki.

Версия языка Python 3.8.5

### Установка и локальный запуск сервера

1. В директории проекта создать новое виртуальное окружение(вручную либо используя IDE)
2. Инициализировать локальный репозиторий и склонировать проект
   ```
   git init
   git clone https://github.com/nemoguigrat/uralintern.git
   ```
3. Перейти `cd uralintern/Uralintern/`
4. Установить зависимости `pip install -r requirements.txt`
5. Создать `Uralintern/.env` c полями
   ```
   SECRET_KEY= #cекретный ключ django
   EMAIL_HOST_USER = #почтовый ящик, который будет использоваться для рассылки
   EMAIL_HOST_PASSWORD = #пароль почтового ящика
   ```
6. Выполнить настройку проекта
   ```
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser 
   ```
7. Запустить сервер 
   `python manage.py runserver`