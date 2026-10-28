from django.urls import path

from . import views

app_name = 'assistant'

urlpatterns = [
    path('assistant/message/', views.message, name='message'),
    path('assistant/voix/', views.voix, name='voix'),
]