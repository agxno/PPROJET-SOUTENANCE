import logging

from django.contrib import admin
from django.views.decorators.cache import never_cache

from .services import donnees_tableau

logger = logging.getLogger(__name__)

admin.site.site_header = "Maison Lumière · Administration"
admin.site.site_title = "Maison Lumière"
admin.site.index_title = "Tableau de bord"

_index_original = admin.site.index


@never_cache
def _index_avec_tableau(request, extra_context=None):
    extra_context = dict(extra_context or {})
    try:
        extra_context['tdb'] = donnees_tableau()
    except Exception:
        # Un souci de calcul ne doit jamais empêcher d'ouvrir l'administration
        logger.exception("Calcul du tableau de bord impossible")
    return _index_original(request, extra_context)


admin.site.index = _index_avec_tableau