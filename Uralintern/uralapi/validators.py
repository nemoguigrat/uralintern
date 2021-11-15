from django.core.exceptions import ValidationError

def is_event_active(model, value):
    if not model.event.is_active and value:
        raise ValidationError("Невозможно активировать этап для закрытого мероприятия")