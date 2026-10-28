import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

URL_REPONSES = "https://api.x.ai/v1/responses"
DELAI = 40


class ErreurGrok(Exception):
    pass


def appeler(charge):
    """Envoie une requête à l'API Responses de xAI et renvoie la réponse décodée."""
    requete = urllib.request.Request(
        URL_REPONSES,
        data=json.dumps(charge).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {settings.XAI_API_KEY}',
            'User-Agent': 'MaisonLumiere/1.0',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(requete, timeout=DELAI) as reponse:
            return json.loads(reponse.read().decode('utf-8'))
    except urllib.error.HTTPError as erreur:
        corps = erreur.read().decode('utf-8', errors='replace')[:500]
        raise ErreurGrok(f"HTTP {erreur.code} : {corps}") from erreur
    except Exception as erreur:
        raise ErreurGrok(f"{type(erreur).__name__} : {erreur}") from erreur


def extraire_texte(reponse):
    morceaux = []
    for element in reponse.get('output', []):
        if element.get('type') == 'message':
            for partie in element.get('content', []):
                texte = partie.get('text')
                if texte:
                    morceaux.append(texte)
    return ' '.join(morceaux).strip()


def extraire_appels(reponse):
    return [e for e in reponse.get('output', []) if e.get('type') == 'function_call']