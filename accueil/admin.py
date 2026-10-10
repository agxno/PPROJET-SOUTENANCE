from django.contrib import admin
from .models import MessageContact
# Register your models here.

@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display = ('nom', 'sujet', 'email', 'date_envoi', 'traitement')
    list_filter = ('traitement', 'date_envoi')
    search_fields = ('nom', 'sujet', 'email')
    list_editable = ('traitement',)