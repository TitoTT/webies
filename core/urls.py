from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import CarrerasSitemap, NoticiasSitemap, PaginasSitemap

sitemaps = {
    'paginas': PaginasSitemap,
    'carreras': CarrerasSitemap,
    'noticias': NoticiasSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('api/contacto/', views.api_contacto, name='api_contacto'),
    path('carreras/<slug:slug>/', views.detalle_carrera, name='detalle_carrera'),
    path('noticias/', views.lista_noticias, name='lista_noticias'),
    path('noticias/<slug:slug>/', views.detalle_noticia, name='detalle_noticia'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]


if settings.DEBUG:
    urlpatterns += [
        path('error-404/', views.preview_404),
        path('error-500/', views.preview_500),
    ]