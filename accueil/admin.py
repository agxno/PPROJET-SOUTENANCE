from django.contrib import admin
from django.utils.html import format_html

from .models import BlocEditorial, MessageContact, Slide


@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'nom', 'email', 'date_envoi', 'traite')
    list_filter = ('traite', 'date_envoi')
    list_editable = ('traite',)
    search_fields = ('nom', 'email', 'sujet')


class ApercuImageMixin:
    @admin.display(description="aperçu")
    def apercu(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px; border-radius:4px;">', obj.image.url)
        return "-"


@admin.register(Slide)
class SlideAdmin(ApercuImageMixin, admin.ModelAdmin):
    list_display = ('titre', 'apercu', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')


@admin.register(BlocEditorial)
class BlocEditorialAdmin(ApercuImageMixin, admin.ModelAdmin):
    list_display = ('titre', 'apercu', 'ordre', 'actif')
    list_editable = ('ordre', 'actif')