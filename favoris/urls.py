from django.urls import path

from . import views

app_name = 'favoris'

urlpatterns = [
    path('favoris/', views.liste, name='liste'),
    path('favoris/basculer/<int:produit_id>/', views.basculer, name='basculer'),
]