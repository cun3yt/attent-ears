from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client

admin.site.register(User, UserAdmin)


class ClientAdmin(admin.ModelAdmin):
    fields = ['name', 'website', 'email_domain', 'keep_in_sync']
    list_display = ('id', 'name', 'website', 'email_domain', 'keep_in_sync')

admin.site.register(Client, ClientAdmin)
