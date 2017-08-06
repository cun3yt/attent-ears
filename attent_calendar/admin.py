from django.contrib import admin
from .models import AttentCalendar


class AttentCalendarAdmin(admin.ModelAdmin):
    fields = ['first_name', 'last_name', 'title', 'email_address', 'timezone']
    list_display = ('id', 'first_name', 'last_name', 'title', 'email_address', 'timezone', 'client', 'google_calendar')

admin.site.register(AttentCalendar, AttentCalendarAdmin)
