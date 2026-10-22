from django.contrib import admin
from django.utils.html import format_html
from .models import Autoridad, Carrera, ConfigInstitucion, Consulta, Noticia

admin.site.site_header = 'IES Trancas · Administración'
admin.site.site_title = 'Admin IES Trancas'
admin.site.index_title = 'Gestión del sitio web'

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'fecha_publicacion', 'destacada')
    list_filter = ('categoria', 'destacada')
    search_fields = ('titulo', 'texto', 'resumen')
    prepopulated_fields = {'slug': ('titulo',)}
    date_hierarchy = 'fecha_publicacion'

    fieldsets = (
        ('Datos principales', {
            'fields': ('titulo', 'slug', 'categoria', 'destacada', 'fecha_publicacion'),
        }),
        ('Contenido', {
            'fields': ('resumen', 'texto', 'autor'),
        }),
        ('Multimedia', {
            'fields': ('imagen',),
        }),
    )


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'duracion', 'tipo_grado', 'muestra_color')
    search_fields = ('nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}

    @admin.display(description="Color")
    def muestra_color(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;'
            'border-radius:4px;background:{};"></span>', obj.color_tematico
        )

    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'slug', 'descripcion', 'duracion'),
        }),
        ('Datos Rápidos (Sidebar)', {
            'fields': ('tipo_grado', 'modalidad', 'ubicacion'),
        }),
        ('Plan de Estudios', {
            'fields': ('perfil_egreso', 'materias', 'salidas_laborales'),
        }),
        ('Inscripciones', {
            'fields': ('inscripciones',),
        }),
        ('Información Adicional', {
            'fields': ('informacion_adicional', 'convenios'),
            'classes': ('collapse',),
        }),
        ('Documentación e Imagen', {
            'fields': ('imagen', 'color_tematico', 'resolucion_pdf', 'plan_estudios_pdf'),
        }),
    )


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'motivo', 'fecha_envio', 'estado')
    list_editable = ('estado',) 
    list_filter = ('estado', 'motivo')
    search_fields = ('nombre', 'email', 'mensaje', 'notas_internas')
    date_hierarchy = 'fecha_envio'
    actions = ['marcar_respondida', 'marcar_pendiente', 'marcar_archivada']


    readonly_fields = ('nombre', 'email_enlace', 'motivo', 'fecha_envio', 'mensaje')
    fieldsets = (
        ('Consulta recibida', {
            'fields': ('nombre', 'email_enlace', 'motivo', 'fecha_envio', 'mensaje'),
        }),
        ('Seguimiento', {
            'fields': ('estado', 'notas_internas'),
        }),
    )

    @admin.display(description='Email')
    def email_enlace(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.email)

    
    def has_add_permission(self, request):
        return False

    def _cambiar_estado(self, request, queryset, estado, texto):
        cantidad = queryset.update(estado=estado)
        self.message_user(request, f'{cantidad} consulta(s) marcada(s) como {texto}.')

    @admin.action(description='Marcar como respondidas')
    def marcar_respondida(self, request, queryset):
        self._cambiar_estado(request, queryset, 'respondida', 'respondidas')

    @admin.action(description='Marcar como pendientes')
    def marcar_pendiente(self, request, queryset):
        self._cambiar_estado(request, queryset, 'pendiente', 'pendientes')

    @admin.action(description='Archivar')
    def marcar_archivada(self, request, queryset):
        self._cambiar_estado(request, queryset, 'archivada', 'archivadas')


@admin.register(ConfigInstitucion)
class ConfigInstitucionAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Datos del instituto', {
            'fields': ('nombre', 'direccion', 'telefono', 'email', 'horario'),
        }),
        ('Ubicación', {
            'fields': ('url_mapa',),
        }),
        ('Estadísticas de la página de inicio', {
            'fields': ('stat_estudiantes', 'stat_docentes', 'stat_anios'),
            'description': 'La cantidad de carreras se calcula sola. Dejá un campo vacío para ocultarlo.',
        }),
        ('Documentos', {
            'fields': ('calendario_academico',),
        }),
    )


    def has_add_permission(self, request):
        return not ConfigInstitucion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False



admin.site.register(Autoridad)