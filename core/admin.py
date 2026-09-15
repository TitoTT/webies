from django.contrib import admin

# Register your models here.
from .models import Noticia, Carrera, Autoridad, Consulta, ConfigInstitucion

# Opción 1: Registrar con personalización (Recomendado para Noticias y Carreras)

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'fecha_publicacion')
    search_fields = ('titulo', 'texto')

@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'duracion')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'motivo', 'fecha_envio', 'estado')
    list_filter = ('estado', 'motivo')
    search_fields = ('nombre', 'email', 'mensaje')

# Opción 2: Registrar simple (Para Autoridades, que es más básico)
# Usamos esta forma simple para evitar errores de herencia si no necesitamos personalizar mucho
admin.site.register(Autoridad)
admin.site.register(ConfigInstitucion)