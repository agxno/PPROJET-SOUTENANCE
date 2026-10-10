from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Adresse, Utilisateur

LABELS_PROFIL = {
    'first_name': 'Prénom',
    'last_name': 'Nom',
    'email': 'E-mail',
    'telephone': 'Téléphone',
}


class InscriptionForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'telephone')
        labels = LABELS_PROFIL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class ConnexionForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'inactive': (
            "Ce compte n'est pas actif. Si vous venez de vous inscrire, cliquez sur le lien "
            "reçu par e-mail, ou demandez un nouveau lien."
        ),
    }


class RenvoiActivationForm(forms.Form):
    email = forms.EmailField(label='E-mail')


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'telephone')
        labels = LABELS_PROFIL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class AdresseForm(forms.ModelForm):
    class Meta:
        model = Adresse
        fields = ('prenom', 'nom', 'adresse', 'ville', 'telephone', 'par_defaut')
        labels = {'par_defaut': 'Définir comme adresse par défaut'}