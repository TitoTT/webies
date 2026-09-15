from django.urls import path
from . import views  # O: from .views import api_noticias

urlpatterns = [
    path('', views.index, name='index'),
    path('api/noticias/', views.api_noticias, name='api_noticias'),
    path('api/carreras/', views.api_carreras, name='api_carreras'),
    path('api/autoridades/', views.api_autoridades, name='api_autoridades'),
    path('api/contacto/', views.api_contacto, name='api_contacto'),
    path('api/config/', views.api_config, name='api_config'),
     path('carreras/<slug:slug>/', views.detalle_carrera, name='detalle_carrera'),
]