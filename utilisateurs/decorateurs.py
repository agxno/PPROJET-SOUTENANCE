from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def connexion_requise(vue):
    """Renvoie un visiteur non connecté vers la connexion, avec un message,
    puis le ramène à sa page d'origine après connexion."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if request.user.is_authenticated:
            return vue(request, *args, **kwargs)

        messages.info(request, "Connectez-vous pour accéder à votre panier et passer commande.")
        if request.method == 'POST':
            suivant = request.POST.get('suivant') or reverse('panier:voir')
        else:
            suivant = request.get_full_path()
        return redirect(f"{reverse('utilisateurs:connexion')}?{urlencode({'next': suivant})}")
    return enveloppe