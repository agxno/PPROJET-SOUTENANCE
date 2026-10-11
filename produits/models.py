from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)

    class Meta:
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class ProduitQuerySet(models.QuerySet):
    def disponibles(self):
        return self.filter(actif=True)

    def nouveautes(self):
        limite = timezone.now() - timedelta(days=30)
        return self.filter(date_creation__gte=limite)

    def promotions(self):
        return self.filter(prix_promo__isnull=False, prix_promo__lt=F('prix'))


class Produit(models.Model):
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='produits')
    nom = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    reference = models.CharField("référence", max_length=30, unique=True)
    description = models.TextField(blank=True)
    prix = models.DecimalField("prix (FCFA)", max_digits=10, decimal_places=0)
    prix_promo = models.DecimalField(
        "prix promo (FCFA)", max_digits=10, decimal_places=0, null=True, blank=True
    )
    image = models.ImageField(upload_to='produits/', blank=True)
    stock = models.PositiveIntegerField(default=0)
    seuil_alerte = models.PositiveIntegerField("seuil de stock faible", default=3)
    actif = models.BooleanField("visible dans la boutique", default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = ProduitQuerySet.as_manager()

    class Meta:
        verbose_name = "produit"
        verbose_name_plural = "produits"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} ({self.reference})"

    def get_absolute_url(self):
        return reverse('produits:detail', kwargs={'slug': self.slug})

    def clean(self):
        if self.prix_promo is not None and self.prix is not None and self.prix_promo >= self.prix:
            raise ValidationError({'prix_promo': "Le prix promo doit être inférieur au prix normal."})

    def save(self, *args, **kwargs):
        if not self.slug:
            # La référence est unique, donc le slug aussi
            self.slug = slugify(f"{self.nom}-{self.reference}")
        super().save(*args, **kwargs)

    @property
    def en_promotion(self):
        return self.prix_promo is not None and self.prix_promo < self.prix

    @property
    def prix_actuel(self):
        return self.prix_promo if self.en_promotion else self.prix

    @property
    def remise(self):
        if not self.en_promotion:
            return 0
        return round(100 * (self.prix - self.prix_promo) / self.prix)

    @property
    def est_nouveau(self):
        return self.date_creation >= timezone.now() - timedelta(days=30)

    @property
    def en_rupture(self):
        return self.stock <= 0

    @property
    def statut_stock(self):
        if self.stock <= 0:
            return 'rupture'
        if self.stock <= self.seuil_alerte:
            return 'faible'
        return 'en_stock'