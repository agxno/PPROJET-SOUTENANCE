from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'accueil'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('a-propos/', views.a_propos, name='a_propos'),
    path('contact/', views.contact, name='contact'),

    path('faq/', TemplateView.as_view(template_name='accueil/faq.html'), name='faq'),
    path('livraison-et-retours/', TemplateView.as_view(template_name='accueil/livraison_retours.html'), name='livraison_retours'),
    path('conditions-generales-de-vente/', TemplateView.as_view(template_name='accueil/cgv.html'), name='cgv'),
    path('mentions-legales/', TemplateView.as_view(template_name='accueil/mentions_legales.html'), name='mentions_legales'),
    path('confidentialite/', TemplateView.as_view(template_name='accueil/confidentialite.html'), name='confidentialite'),
]