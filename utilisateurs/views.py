from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.http import require_POST

from .courriels import envoyer_mail_activation
from .forms import AdresseForm, InscriptionForm, ProfilForm, RenvoiActivationForm
from .jetons import jeton_activation
from .models import Utilisateur


def inscription(request):
    if request.user.is_authenticated:
        return redirect('utilisateurs:tableau_bord')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            utilisateur = form.save(commit=False)
            utilisateur.is_active = False
            utilisateur.save()
            try:
                envoyer_mail_activation(request, utilisateur)
            except Exception:
                # Pas de compte "fantôme" si l'e-mail n'a pas pu partir
                utilisateur.delete()
                messages.error(
                    request,
                    "L'e-mail de validation n'a pas pu être envoyé. Vérifiez votre adresse et réessayez."
                )
            else:
                return redirect('utilisateurs:activation_envoyee')
    else:
        form = InscriptionForm()
    return render(request, 'utilisateurs/inscription.html', {'form': form})


def activation(request, uidb64, token):
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        utilisateur = Utilisateur.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        utilisateur = None

    if utilisateur is not None and jeton_activation.check_token(utilisateur, token):
        utilisateur.is_active = True
        utilisateur.save(update_fields=['is_active'])
        login(request, utilisateur)
        messages.success(request, "Votre compte est activé. Bienvenue !")
        return redirect('utilisateurs:tableau_bord')

    return render(request, 'utilisateurs/activation_invalide.html')


def renvoyer_activation(request):
    if request.method == 'POST':
        form = RenvoiActivationForm(request.POST)
        if form.is_valid():
            utilisateur = Utilisateur.objects.filter(
                email__iexact=form.cleaned_data['email'], is_active=False
            ).first()
            if utilisateur is not None:
                try:
                    envoyer_mail_activation(request, utilisateur)
                except Exception:
                    messages.error(request, "L'envoi a échoué. Réessayez dans quelques instants.")
                    return render(request, 'utilisateurs/renvoyer_activation.html', {'form': form})
            # Même réponse que le compte existe ou non (on ne révèle rien)
            return redirect('utilisateurs:activation_envoyee')
    else:
        form = RenvoiActivationForm()
    return render(request, 'utilisateurs/renvoyer_activation.html', {'form': form})


@login_required
def tableau_bord(request):
    from commandes.models import Commande
    from favoris.models import Favori
    from django.db.models import Sum

    adresse = request.user.adresses.filter(par_defaut=True).first()
    commandes = request.user.commandes.all()
    derniere = commandes.first()

    # Stats
    total_commandes = commandes.count()
    en_cours = commandes.filter(
        statut__in=['en_attente', 'en_preparation', 'expediee']
    ).count()
    total_depense = commandes.filter(
        statut__in=['en_preparation', 'expediee', 'livree']
    ).aggregate(total=Sum('total'))['total'] or 0
    nb_favoris = Favori.objects.filter(utilisateur=request.user).count()
    nb_adresses = request.user.adresses.count()

    # Dernières commandes (4 max)
    dernieres_commandes = commandes[:4]

    # Derniers favoris (4 max)
    derniers_favoris = Favori.objects.filter(
        utilisateur=request.user
    ).select_related('produit', 'produit__categorie')[:4]

    return render(request, 'utilisateurs/tableau_bord.html', {
        'adresse': adresse,
        'derniere': derniere,
        'total_commandes': total_commandes,
        'en_cours': en_cours,
        'total_depense': total_depense,
        'nb_favoris': nb_favoris,
        'nb_adresses': nb_adresses,
        'dernieres_commandes': dernieres_commandes,
        'derniers_favoris': derniers_favoris,
    })


@login_required
def mes_informations(request):
    profil_form = ProfilForm(instance=request.user)
    mdp_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profil':
            profil_form = ProfilForm(request.POST, instance=request.user)
            if profil_form.is_valid():
                profil_form.save()
                messages.success(request, "Vos informations ont été mises à jour.")
                return redirect('utilisateurs:mes_informations')
        elif action == 'mot_de_passe':
            mdp_form = PasswordChangeForm(request.user, request.POST)
            if mdp_form.is_valid():
                utilisateur = mdp_form.save()
                update_session_auth_hash(request, utilisateur)
                messages.success(request, "Votre mot de passe a été modifié.")
                return redirect('utilisateurs:mes_informations')

    return render(request, 'utilisateurs/mes_informations.html', {
        'profil_form': profil_form,
        'mdp_form': mdp_form,
    })


@login_required
def mes_adresses(request):
    if request.method == 'POST':
        form = AdresseForm(request.POST)
        if form.is_valid():
            adresse = form.save(commit=False)
            adresse.utilisateur = request.user
            adresse.save()
            messages.success(request, "Adresse ajoutée.")
            return redirect('utilisateurs:mes_adresses')
    else:
        form = AdresseForm()
    return render(request, 'utilisateurs/mes_adresses.html', {
        'adresses': request.user.adresses.all(),
        'form': form,
    })


@login_required
def modifier_adresse(request, pk):
    adresse = get_object_or_404(request.user.adresses, pk=pk)
    if request.method == 'POST':
        form = AdresseForm(request.POST, instance=adresse)
        if form.is_valid():
            form.save()
            messages.success(request, "Adresse modifiée.")
            return redirect('utilisateurs:mes_adresses')
    else:
        form = AdresseForm(instance=adresse)
    return render(request, 'utilisateurs/modifier_adresse.html', {'form': form})


@login_required
@require_POST
def supprimer_adresse(request, pk):
    adresse = get_object_or_404(request.user.adresses, pk=pk)
    adresse.delete()
    messages.success(request, "Adresse supprimée.")
    return redirect('utilisateurs:mes_adresses')