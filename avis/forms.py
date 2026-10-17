from django import forms

from .models import Avis


class AvisForm(forms.ModelForm):
    note = forms.TypedChoiceField(
        label="Votre note",
        choices=[(i, i) for i in range(5, 0, -1)],
        coerce=int,
        widget=forms.RadioSelect,
        error_messages={'required': "Choisissez une note de 1 à 5 étoiles."},
    )

    class Meta:
        model = Avis
        fields = ('note', 'titre', 'commentaire')
        labels = {'titre': "Titre de l'avis", 'commentaire': "Votre commentaire"}
        widgets = {
            'titre': forms.TextInput(attrs={'maxlength': 120, 'autocomplete': 'off'}),
            'commentaire': forms.Textarea(attrs={'rows': 5, 'maxlength': 2000}),
        }

    def clean_titre(self):
        titre = self.cleaned_data['titre'].strip()
        if len(titre) < 3:
            raise forms.ValidationError("Le titre est trop court (3 caractères minimum).")
        return titre

    def clean_commentaire(self):
        commentaire = self.cleaned_data['commentaire'].strip()
        if len(commentaire) < 10:
            raise forms.ValidationError("Votre commentaire est un peu court (10 caractères minimum).")
        return commentaire