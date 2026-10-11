from django.urls import path

from . import views

app_name = 'commandes'

urlpatterns = [
    path('commande/', views.valider, name='valider'),
    path('compte/commandes/', views.liste, name='liste'),
    path('compte/commandes/<str:reference>/', views.detail, name='detail'),
    path('compte/commandes/<str:reference>/confirmation/', views.confirmation, name='confirmation'),
    path('compte/commandes/<str:reference>/annuler/', views.annuler, name='annuler'),
]