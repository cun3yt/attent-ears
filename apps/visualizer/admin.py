from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.admin import AttentAdminModel

from .models import User, Client, CLIENT_STATUS_CHOICES


class AttentUserAdmin(UserAdmin, AttentAdminModel):
    readonly_fields = ('email')


admin.site.register(User, AttentUserAdmin)
admin.site.disable_action('delete_selected')


class ClientForm(forms.ModelForm):
    status = forms.ChoiceField(choices=CLIENT_STATUS_CHOICES)


class ClientAdmin(AttentAdminModel):
    readonly_fields = ('email_domain',)

    fields = ['email_domain', 'name', 'website', 'status']
    list_display = ('id', 'name', 'website', 'email_domain', 'status')
    form = ClientForm

admin.site.register(Client, ClientAdmin)
