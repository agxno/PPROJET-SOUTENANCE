from django.contrib.auth.tokens import PasswordResetTokenGenerator


class GenerateurJetonActivation(PasswordResetTokenGenerator):
    # Sel distinct : un jeton d'activation ne peut pas servir à réinitialiser un mot de passe
    key_salt = 'utilisateurs.jetons.GenerateurJetonActivation'

    def _make_hash_value(self, user, timestamp):
        # Inclut is_active : le lien devient invalide dès que le compte est activé
        return f'{user.pk}{user.is_active}{timestamp}'


jeton_activation = GenerateurJetonActivation()