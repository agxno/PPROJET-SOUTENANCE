from django.urls import path

from . import views

app_name = 'paiements'

urlpatterns = [
    path('compte/commandes/<str:reference>/payer/', views.payer, name='payer'),

    # Kadev Pay (la notification doit rester avant la route à paramètre)
    path('paiement/kadev/notification/', views.webhook_kadev, name='webhook_kadev'),
    path('paiement/kadev/<str:transaction_id>/', views.kadev_checkout, name='kadev'),
    path('paiement/kadev/<str:transaction_id>/confirmer/', views.kadev_confirmer, name='kadev_confirmer'),
    path('paiement/retour/<str:transaction_id>/', views.retour, name='retour'),

    # Simulation
    path('paiement/simulation/<str:transaction_id>/', views.simulation, name='simulation'),
    path('paiement/simulation/<str:transaction_id>/resultat/', views.simulation_resultat, name='simulation_resultat'),
]