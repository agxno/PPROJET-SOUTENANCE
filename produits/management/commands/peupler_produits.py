from django.core.management.base import BaseCommand

from produits.models import Categorie, Produit

CATALOGUE = {
    'Bagues': [
        ('BAG-001', 'Bague Aurore', 45000, None, 12),
        ('BAG-002', 'Bague Solstice', 62000, 49000, 5),
        ('BAG-003', 'Bague Éclipse', 78000, None, 0),
    ],
    'Colliers': [
        ('COL-001', 'Collier Étoile', 54000, None, 8),
        ('COL-002', 'Collier Perle', 89000, 71000, 2),
        ('COL-003', 'Collier Lune', 66000, None, 15),
    ],
    'Bracelets': [
        ('BRA-001', 'Bracelet Lumière', 38000, None, 20),
        ('BRA-002', 'Bracelet Rivière', 72000, 58000, 6),
        ('BRA-003', "Bracelet Fil d'Or", 49000, None, 3),
    ],
    "Boucles d'oreilles": [
        ('BOU-001', 'Boucles Cristal', 36000, None, 10),
        ('BOU-002', 'Boucles Opale', 58000, 46000, 4),
        ('BOU-003', 'Boucles Comète', 42000, None, 9),
    ],
}


class Command(BaseCommand):
    help = "Crée des catégories et des produits de démonstration (sans photos)."

    def handle(self, *args, **options):
        crees = 0
        for nom_categorie, produits in CATALOGUE.items():
            categorie, _ = Categorie.objects.get_or_create(nom=nom_categorie)
            for reference, nom, prix, prix_promo, stock in produits:
                _, cree = Produit.objects.get_or_create(
                    reference=reference,
                    defaults={
                        'categorie': categorie,
                        'nom': nom,
                        'description': f"{nom} : une création Maison Lumière, finition soignée.",
                        'prix': prix,
                        'prix_promo': prix_promo,
                        'stock': stock,
                    },
                )
                crees += int(cree)
        self.stdout.write(self.style.SUCCESS(f"{crees} produit(s) créé(s)."))