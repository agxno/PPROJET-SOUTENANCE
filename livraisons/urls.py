from django.urls import path

from . import views

app_name = 'livraisons'

urlpatterns = [
    path('livreur/', views.tableau, name='tableau'),
    path('livreur/commandes/<str:reference>/', views.detail, name='detail'),
    path('livreur/commandes/<str:reference>/statut/', views.changer_statut, name='changer_statut'),
]