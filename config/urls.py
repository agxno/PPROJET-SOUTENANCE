from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accueil.urls')),
    path('', include('utilisateurs.urls')),
    path('', include('produits.urls')),
    path('', include('panier.urls')),
    path('', include('commandes.urls')),
    path('', include('paiements.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)