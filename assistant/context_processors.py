from django.conf import settings


def assistant(request):
    return {
        'assistant_actif': settings.ASSISTANT_ACTIF,
        'assistant_mode': settings.ASSISTANT_MODE,
    }