from django.contrib.auth.views import LoginView, PasswordResetView
from django.urls import reverse

from .liens import contexte_lien_reinitialisation


class ConnexionView(LoginView):
    def get_default_redirect_url(self):
        utilisateur = self.request.user
        if utilisateur.is_authenticated and utilisateur.est_livreur:
            return reverse('livraisons:tableau')
        return super().get_default_redirect_url()


class ReinitialisationView(PasswordResetView):
    """Même vue que celle de Django, mais le lien reçu par e-mail utilise SITE_URL."""

    @property
    def extra_email_context(self):
        return contexte_lien_reinitialisation()