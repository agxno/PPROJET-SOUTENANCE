from django.core.management.base import BaseCommand

from accueil.models import BlocEditorial, Slide


class Command(BaseCommand):
    help = "Crée des diapositives et des blocs de démonstration pour l'accueil (sans photos)."

    def handle(self, *args, **options):
        if not Slide.objects.exists():
            Slide.objects.bulk_create([
                Slide(etiquette="Nouvelle collection", titre="L'éclat qui vous ressemble",
                      texte="Des bijoux élégants, à offrir ou à s'offrir.",
                      bouton_texte="Découvrir la boutique", bouton_lien="/boutique/", ordre=1),
                Slide(etiquette="Offres du moment", titre="Des promotions à ne pas manquer",
                      texte="Une sélection de bijoux à prix réduit, pour une durée limitée.",
                      bouton_texte="Voir les promotions", bouton_lien="/promotions/", ordre=2),
                Slide(etiquette="Nouveautés", titre="Les dernières créations de la maison",
                      texte="Découvrez les pièces arrivées ce mois-ci.",
                      bouton_texte="Voir les nouveautés", bouton_lien="/nouveautes/", ordre=3),
            ])
        if not BlocEditorial.objects.exists():
            BlocEditorial.objects.bulk_create([
                BlocEditorial(etiquette="Notre savoir-faire", titre="Chaque pièce raconte une histoire",
                              texte="Nos bijoux sont choisis pour la qualité de leur finition et la justesse de leur dessin, afin de vous accompagner longtemps.",
                              bouton_texte="En savoir plus", bouton_lien="/a-propos/", ordre=1),
                BlocEditorial(etiquette="L'art d'offrir", titre="Le cadeau parfait, sans hésitation",
                              texte="Pour une naissance, un anniversaire ou une demande, trouvez le bijou qui dira tout ce que les mots ne disent pas.",
                              bouton_texte="Voir la boutique", bouton_lien="/boutique/",
                              image_a_droite=True, ordre=2),
            ])
        self.stdout.write(self.style.SUCCESS("Accueil de démonstration créé."))