from django.db import models


class MessageContact(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    sujet = models.CharField(max_length=150)
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    class Meta:
        verbose_name = "message de contact"
        verbose_name_plural = "messages de contact"
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.sujet} - {self.nom}"


class Slide(models.Model):
    etiquette = models.CharField("sur-titre", max_length=60, blank=True)
    titre = models.CharField(max_length=120)
    texte = models.CharField(max_length=220, blank=True)
    image = models.ImageField(
        upload_to='slides/', blank=True,
        help_text="Format paysage conseillé : 1920 x 900 px, moins de 400 Ko.",
    )
    bouton_texte = models.CharField("texte du bouton", max_length=40, blank=True, default="Découvrir")
    bouton_lien = models.CharField(
        "lien du bouton", max_length=200, blank=True, default="/boutique/",
        help_text="Par exemple : /boutique/, /promotions/, /nouveautes/ ou /a-propos/",
    )
    ordre = models.PositiveSmallIntegerField(default=1, help_text="Les plus petits numéros s'affichent en premier.")
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "diapositive d'accueil"
        verbose_name_plural = "diapositives d'accueil"
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre


class BlocEditorial(models.Model):
    etiquette = models.CharField("sur-titre", max_length=60, blank=True)
    titre = models.CharField(max_length=120)
    texte = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='blocs/', blank=True,
        help_text="Format portrait conseillé : 1000 x 1250 px, moins de 400 Ko.",
    )
    bouton_texte = models.CharField("texte du bouton", max_length=40, blank=True)
    bouton_lien = models.CharField("lien du bouton", max_length=200, blank=True)
    image_a_droite = models.BooleanField("image à droite", default=False)
    ordre = models.PositiveSmallIntegerField(default=1, help_text="Les plus petits numéros s'affichent en premier.")
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "bloc de présentation"
        verbose_name_plural = "blocs de présentation"
        ordering = ['ordre', 'id']

    def __str__(self):
        return self.titre