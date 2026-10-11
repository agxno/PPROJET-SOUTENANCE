from django.urls import path

from . import views

app_name = 'panier'

urlpatterns = [
    path('panier/', views.voir, name='voir'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter, name='ajouter'),
    path('panier/ligne/<int:ligne_id>/modifier/', views.modifier, name='modifier'),
    path('panier/ligne/<int:ligne_id>/retirer/', views.retirer, name='retirer'),
]