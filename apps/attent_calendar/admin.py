from django.contrib import admin
from core.admin import AttentAdminModel
from .models import AttentCalendar


class AttentCalendarAdmin(AttentAdminModel):
    fields = ['first_name', 'last_name', 'title', 'email_address', 'timezone']
    list_display = ('id', 'first_name', 'last_name', 'title', 'email_address', 'timezone', 'client', 'google_calendar')

admin.site.register(AttentCalendar, AttentCalendarAdmin)
