from django.contrib.auth.views import LoginView
from django.urls import reverse


class ConnexionView(LoginView):
    def get_default_redirect_url(self):
        utilisateur = self.request.user
        if utilisateur.is_authenticated and utilisateur.est_livreur:
            return reverse('livraisons:tableau')
        return super().get_default_redirect_url()