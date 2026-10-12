from functools import wraps
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def livreur_requis(vue):
    """Connexion obligatoire, puis accès réservé aux comptes livreur."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_authenticated:
            suivant = urlencode({'next': request.get_full_path()})
            return redirect(f"{reverse('utilisateurs:connexion')}?{suivant}")
        if not request.user.est_livreur:
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return enveloppe