from django.urls import path

from . import views

app_name = 'paiements'

urlpatterns = [
    path('compte/commandes/<str:reference>/payer/', views.payer, name='payer'),
    path('paiement/retour/<str:transaction_id>/', views.retour, name='retour'),
    path('paiement/cinetpay/notification/', views.webhook_cinetpay, name='webhook_cinetpay'),
]