from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView

from . import views
from .connexion import ConnexionView
from .forms import ConnexionForm

app_name = 'utilisateurs'

urlpatterns = [
    path('connexion/', ConnexionView.as_view(
        template_name='utilisateurs/connexion.html',
        authentication_form=ConnexionForm,
        redirect_authenticated_user=True,
    ), name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='deconnexion'),

    path('inscription/', views.inscription, name='inscription'),
    path('inscription/envoyee/', TemplateView.as_view(
        template_name='utilisateurs/activation_envoyee.html',
    ), name='activation_envoyee'),
    path('activation/renvoyer/', views.renvoyer_activation, name='renvoyer_activation'),
    path('activation/<uidb64>/<token>/', views.activation, name='activation'),

    path('mot-de-passe-oublie/', auth_views.PasswordResetView.as_view(
        template_name='utilisateurs/mot_de_passe_oublie.html',
        email_template_name='utilisateurs/emails/reinitialisation.txt',
        subject_template_name='utilisateurs/emails/sujet_reinitialisation.txt',
        success_url=reverse_lazy('utilisateurs:mot_de_passe_envoye'),
    ), name='mot_de_passe_oublie'),
    path('mot-de-passe-oublie/envoye/', auth_views.PasswordResetDoneView.as_view(
        template_name='utilisateurs/mot_de_passe_envoye.html',
    ), name='mot_de_passe_envoye'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='utilisateurs/nouveau_mot_de_passe.html',
        success_url=reverse_lazy('utilisateurs:reinitialisation_terminee'),
    ), name='reinitialiser'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(
        template_name='utilisateurs/reinitialisation_terminee.html',
    ), name='reinitialisation_terminee'),

    path('compte/', views.tableau_bord, name='tableau_bord'),
    path('compte/informations/', views.mes_informations, name='mes_informations'),
    path('compte/adresses/', views.mes_adresses, name='mes_adresses'),
    path('compte/adresses/<int:pk>/modifier/', views.modifier_adresse, name='modifier_adresse'),
    path('compte/adresses/<int:pk>/supprimer/', views.supprimer_adresse, name='supprimer_adresse'),
]