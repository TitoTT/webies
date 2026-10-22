from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Carrera, Noticia


class PaginasSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 1.0

    def items(self):
        return ['index', 'lista_noticias']

    def location(self, item):
        return reverse(item)


class CarrerasSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return Carrera.objects.exclude(slug='')


class NoticiasSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Noticia.objects.exclude(slug='')

    def lastmod(self, obj):
        return obj.fecha_publicacion