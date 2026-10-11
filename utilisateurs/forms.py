from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Adresse, Utilisateur

LABELS_PROFIL = {
    'first_name': 'Prénom',
    'last_name': 'Nom',
    'email': 'E-mail',
    'telephone': 'Téléphone',
}

# Empêche le navigateur de préremplir un champ : il reste en lecture seule
# jusqu'au clic de l'utilisateur dedans
ANTI_AUTOFILL = {
    'autocomplete': 'off',
    'readonly': 'readonly',
    'onfocus': "this.removeAttribute('readonly');",
}
ANTI_AUTOFILL_MDP = {**ANTI_AUTOFILL, 'autocomplete': 'new-password'}


class InscriptionForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ('first_name', 'last_name', 'email', 'telephone')
        labels = LABELS_PROFIL

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        for nom in ('first_name', 'last_name', 'email', 'telephone'):
            self.fields[nom].widget.attrs.update(ANTI_AUTOFILL)
        for nom in ('password1', 'password2'):
            self.fields[nom].widget.attrs.update(ANTI_AUTOFILL_MDP)


class ConnexionForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'inactive': (
            "Ce compte n'est pas actif. Si vous venez de vous inscrire, cliquez sur le lien "
            "reçu par e-mail, ou demandez un nouveau lien."
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sans autofocus : un focus automatique retirerait la protection au chargement
        self.fields['username'].widget.attrs.pop('autofocus', None)
        self.fields['username'].widget.attrs.update(ANTI_AUTOFILL)
        self.fields['password'].widget.attrs.update(ANTI_AUTOFILL_MDP)


class RenvoiActivationForm(forms.Form):
    email = forms.EmailField(label='E-mail')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update(ANTI_AUTOFILL)


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