from urllib.parse import urlsplit

from django.conf import settings


def adresse_absolue(request, chemin):
    """Adresse complète d'une page pour les e-mails.
    Utilise SITE_URL (adresse publique du site) si elle est définie dans .env ;
    sinon, l'adresse depuis laquelle la demande a été faite."""
    if settings.SITE_URL:
        return settings.SITE_URL + chemin
    return request.build_absolute_uri(chemin)


def contexte_lien_reinitialisation():
    """Protocole et domaine à utiliser dans l'e-mail de réinitialisation du mot de passe."""
    if not settings.SITE_URL:
        return None
    morceaux = urlsplit(settings.SITE_URL)
    return {'protocol': morceaux.scheme, 'domain': morceaux.netloc}