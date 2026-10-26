from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

MESSAGE_PAR_DEFAUT = "Connectez-vous pour accéder à votre panier et passer commande."


def connexion_requise(vue=None, *, message=MESSAGE_PAR_DEFAUT):
    """Renvoie un visiteur non connecté vers la connexion, avec un message,
    puis le ramène à sa page d'origine après connexion.
    S'utilise avec ou sans parenthèses : @connexion_requise ou @connexion_requise(message="...")."""
    def decorateur(fonction):
        @wraps(fonction)
        def enveloppe(request, *args, **kwargs):
            if request.user.is_authenticated:
                return fonction(request, *args, **kwargs)

            messages.info(request, message)
            if request.method == 'POST':
                suivant = request.POST.get('suivant') or reverse('panier:voir')
            else:
                suivant = request.get_full_path()
            return redirect(f"{reverse('utilisateurs:connexion')}?{urlencode({'next': suivant})}")
        return enveloppe

    if vue is not None:
        return decorateur(vue)
    return decorateur