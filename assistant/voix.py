import hashlib
import re

import edge_tts
from django.conf import settings
from django.core.cache import cache

EMOJIS = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]')


def nettoyer_pour_voix(texte):
    texte = re.sub(r'https?://\S+', '', texte or '')
    texte = EMOJIS.sub('', texte)
    texte = re.sub(r'[*_#`>~|]+', '', texte)
    texte = re.sub(r'\bFCFA\b', 'francs CFA', texte)
    return re.sub(r'\s+', ' ', texte).strip()


def synthetiser(texte):
    """Transforme un texte en audio MP3 avec Edge TTS (les phrases déjà dites sont gardées en mémoire)."""
    cle = 'assistant:tts:' + hashlib.sha256(f'{settings.ASSISTANT_VOIX}|{texte}'.encode('utf-8')).hexdigest()
    audio = cache.get(cle)
    if audio:
        return audio
    communication = edge_tts.Communicate(texte, settings.ASSISTANT_VOIX)
    audio = b''.join(m['data'] for m in communication.stream_sync() if m['type'] == 'audio')
    if not audio:
        raise RuntimeError("Edge TTS n'a renvoyé aucun son.")
    cache.set(cle, audio, 3600)
    return audio