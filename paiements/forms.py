import re

from django import forms

from .models import Paiement

METHODES_FORMULAIRE = [
    ('mobile_money', 'Mobile money'),
    ('carte', 'Carte bancaire'),
]


class MethodeForm(forms.Form):
    """Choix du moyen de paiement avant d'ouvrir Kadev Pay."""
    methode = forms.ChoiceField(
        label="Moyen de paiement",
        choices=METHODES_FORMULAIRE,
        widget=forms.RadioSelect,
        initial='mobile_money',
    )


class PaiementForm(forms.Form):
    """Formulaire de la simulation (démonstration locale)."""
    methode = forms.ChoiceField(
        label="Moyen de paiement",
        choices=METHODES_FORMULAIRE,
        widget=forms.RadioSelect,
        initial='mobile_money',
    )
    operateur = forms.ChoiceField(
        label="Opérateur",
        choices=Paiement.OPERATEURS,
        widget=forms.RadioSelect,
        required=False,
        initial='orange',
    )
    telephone = forms.CharField(
        label="Numéro de téléphone",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '07 00 00 00 00',
            'inputmode': 'tel',
            'autocomplete': 'off',
        }),
    )

    def clean(self):
        donnees = super().clean()
        if donnees.get('methode') == 'mobile_money':
            if not donnees.get('operateur'):
                self.add_error('operateur', "Choisissez un opérateur.")
            telephone = re.sub(r'[\s.\-]', '', donnees.get('telephone') or '')
            if re.fullmatch(r'\+?\d{8,15}', telephone):
                donnees['telephone'] = telephone
            else:
                self.add_error('telephone', "Saisissez un numéro valide (8 à 15 chiffres).")
        else:
            donnees['operateur'] = ''
            donnees['telephone'] = ''
        return donnees