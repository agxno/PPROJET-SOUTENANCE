from django.urls import path

from . import views

app_name = 'produits'

urlpatterns = [
    path('boutique/', views.liste, name='liste'),
    path('nouveautes/', views.nouveautes, name='nouveautes'),
    path('promotions/', views.promotions, name='promotions'),
    path('boutique/<slug:slug>/', views.detail, name='detail'),
]