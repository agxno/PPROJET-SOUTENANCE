import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import grok
from .services import converser
from .voix import nettoyer_pour_voix, synthetiser

logger = logging.getLogger(__name__)

MAX_MESSAGE = 300
MAX_VOIX = 500
MESSAGES_PAR_MINUTE = 10
MESSAGES_PAR_JOUR = 120
MESSAGES_PAR_JOUR_TOTAL = 1000
VOIX_PAR_MINUTE = 30


def _identite(request):
    if request.user.is_authenticated:
        return f"u{request.user.pk}"
    return "ip" + request.META.get('REMOTE_ADDR', 'inconnue')


def _autorise(cle, maximum, fenetre):
    cache.add(cle, 0, fenetre)
    try:
        compteur = cache.incr(cle)
    except ValueError:
        cache.set(cle, 1, fenetre)
        compteur = 1
    return compteur <= maximum


def _erreur(texte, statut):
    return JsonResponse({'reponse': texte, 'actions': [], 'erreur': True}, status=statut)


def _nettoyer_historique(brut):
    historique = []
    if isinstance(brut, list):
        for element in brut[-6:]:
            if (
                isinstance(element, dict)
                and element.get('role') in ('user', 'assistant')
                and isinstance(element.get('content'), str)
            ):
                contenu = element['content'].strip()[:500]
                if contenu:
                    historique.append({'role': element['role'], 'content': contenu})
    return historique


def _lire_json(request):
    try:
        donnees = json.loads(request.body)
    except ValueError:
        return None
    return donnees if isinstance(donnees, dict) else None


@require_POST
def message(request):
    if not settings.ASSISTANT_ACTIF:
        return _erreur("L'assistant vocal n'est pas disponible pour le moment.", 503)

    identite = _identite(request)
    jour = timezone.localdate().isoformat()
    if not (
        _autorise(f'assistant:min:{identite}', MESSAGES_PAR_MINUTE, 60)
        and _autorise(f'assistant:jour:{identite}:{jour}', MESSAGES_PAR_JOUR, 86400)
    ):
        return _erreur("Vous allez un peu vite. Patientez un instant avant de me reparler.", 429)
    if not _autorise(f'assistant:total:{jour}', MESSAGES_PAR_JOUR_TOTAL, 86400):
        return _erreur("L'assistant a atteint sa limite pour aujourd'hui. Revenez demain.", 429)

    donnees = _lire_json(request)
    if donnees is None:
        return _erreur("Demande invalide.", 400)
    texte = str(donnees.get('message', '')).strip()[:MAX_MESSAGE]
    if not texte:
        return _erreur("Je n'ai rien entendu.", 400)

    historique = _nettoyer_historique(donnees.get('historique'))
    page = str(donnees.get('page', ''))[:200]
    try:
        reponse, actions = converser(request, texte, historique, page)
    except grok.ErreurGrok:
        logger.exception("Échec de l'appel à Grok")
        return _erreur("Je n'arrive pas à répondre pour le moment. Réessayez dans un instant.", 502)
    return JsonResponse({'reponse': reponse, 'actions': actions})


@require_POST
def voix(request):
    if not _autorise(f'assistant:voix:{_identite(request)}', VOIX_PAR_MINUTE, 60):
        return HttpResponse(status=429)
    donnees = _lire_json(request)
    texte = nettoyer_pour_voix(str((donnees or {}).get('texte', '')))[:MAX_VOIX]
    if not texte:
        return HttpResponse(status=400)
    try:
        audio = synthetiser(texte)
    except Exception:
        logger.exception("Échec de la synthèse vocale Edge TTS")
        return HttpResponse(status=502)
    return HttpResponse(audio, content_type='audio/mpeg')