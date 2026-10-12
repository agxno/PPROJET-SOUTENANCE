from django.urls import path

from . import views

app_name = 'paiements'

urlpatterns = [
    path('compte/commandes/<str:reference>/payer/', views.payer, name='payer'),
    path('paiement/simulation/<str:transaction_id>/', views.simulation, name='simulation'),
    path('paiement/simulation/<str:transaction_id>/resultat/', views.simulation_resultat, name='simulation_resultat'),
]