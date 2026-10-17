from django.urls import path

from . import views

app_name = 'avis'

urlpatterns = [
    path('boutique/<slug:slug>/avis/', views.laisser, name='laisser'),
]