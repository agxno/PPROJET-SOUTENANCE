from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from assistant import comprehension, grok, voix


class Command(BaseCommand):
    help = "Teste l'assistant vocal : cerveau (règles ou Grok) et voix (Edge TTS)."

    def add_arguments(self, parser):
        parser.add_argument('--phrase', help="Essaie une phrase, comme si un visiteur non connecté la disait.")

    def handle(self, *args, **options):
        self.stdout.write(f"Mode : {settings.ASSISTANT_MODE}")

        if options['phrase']:
            requete = RequestFactory().get('/')
            requete.user = AnonymousUser()
            reponse, actions = comprehension.repondre(requete, options['phrase'], '/')
            self.stdout.write(self.style.SUCCESS(f"Réponse : {reponse}"))
            self.stdout.write(f"Actions : {actions}")
            return

        if settings.ASSISTANT_MODE == 'grok':
            if not settings.XAI_API_KEY:
                self.stdout.write(self.style.ERROR("Grok : XAI_API_KEY est absente du fichier .env."))
            else:
                try:
                    reponse = grok.appeler({
                        "model": settings.XAI_MODEL,
                        "input": [
                            {"role": "system", "content": "Tu réponds toujours très brièvement, en français."},
                            {"role": "user", "content": "Dis seulement : OK"},
                        ],
                    })
                    texte = grok.extraire_texte(reponse) or "(réponse vide)"
                    self.stdout.write(self.style.SUCCESS(f"Grok ({settings.XAI_MODEL}) : {texte}"))
                except grok.ErreurGrok as erreur:
                    self.stdout.write(self.style.ERROR(f"Grok : {erreur}"))
        else:
            self.stdout.write(self.style.SUCCESS("Cerveau : règles intégrées à Django, rien à configurer."))

        try:
            audio = voix.synthetiser("Bonjour, ceci est un test de la voix.")
            self.stdout.write(self.style.SUCCESS(f"Edge TTS ({settings.ASSISTANT_VOIX}) : {len(audio)} octets reçus"))
        except Exception as erreur:
            self.stdout.write(self.style.ERROR(f"Edge TTS : {type(erreur).__name__} : {erreur}"))