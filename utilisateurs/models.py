from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class GestionnaireUtilisateur(BaseUserManager):
    use_in_migrations = True

    def _creer(self, email, password, **champs):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        utilisateur = self.model(email=self.normalize_email(email), **champs)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_user(self, email, password=None, **champs):
        champs.setdefault('is_staff', False)
        champs.setdefault('is_superuser', False)
        return self._creer(email, password, **champs)

    def create_superuser(self, email, password=None, **champs):
        champs.setdefault('is_staff', True)
        champs.setdefault('is_superuser', True)
        return self._creer(email, password, **champs)


class Utilisateur(AbstractUser):
    username = None
    email = models.EmailField("adresse e-mail", unique=True)
    telephone = models.CharField("téléphone", max_length=20, blank=True)
    est_livreur = models.BooleanField(
        "livreur", default=False,
        help_text="Donne accès à l'espace livreur. Les livreurs sont créés par l'administration.",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = GestionnaireUtilisateur()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return self.email


class Adresse(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='adresses'
    )
    prenom = models.CharField("prénom", max_length=100)
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    telephone = models.CharField("téléphone", max_length=20)
    par_defaut = models.BooleanField("adresse par défaut", default=False)

    class Meta:
        verbose_name = "adresse"
        verbose_name_plural = "adresses"
        ordering = ['-par_defaut', '-id']

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.ville}"

    def save(self, *args, **kwargs):
        # La première adresse d'un client est automatiquement celle par défaut
        if not self.utilisateur.adresses.exclude(pk=self.pk).exists():
            self.par_defaut = True
        super().save(*args, **kwargs)
        # Une seule adresse par défaut par client
        if self.par_defaut:
            self.utilisateur.adresses.exclude(pk=self.pk).update(par_defaut=False)