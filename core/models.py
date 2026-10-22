import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image, ImageOps

def slug_unico(modelo, texto, instancia, largo_max):
    base = slugify(texto)[:largo_max - 10].strip('-') or modelo.__name__.lower()
    slug = base
    contador = 2
    while modelo.objects.filter(slug=slug).exclude(pk=instancia.pk).exists():
        slug = f'{base}-{contador}'
        contador += 1
    return slug

def optimizar_imagen(campo, max_lado=1600, calidad=82):
    if not campo or campo._committed:
        return
    try:
        campo.file.seek(0)
        img = Image.open(campo.file)
        formato = img.format
        if formato not in ('JPEG', 'PNG', 'WEBP'):
            campo.file.seek(0)
            return

        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_lado, max_lado))

        buffer = BytesIO()
        if formato == 'PNG':
            img.save(buffer, format='PNG', optimize=True)
            extension = '.png'
        elif formato == 'WEBP':
            img.save(buffer, format='WEBP', quality=calidad)
            extension = '.webp'
        else:
            img.convert('RGB').save(buffer, format='JPEG', quality=calidad, optimize=True)
            extension = '.jpg'

        nombre = os.path.splitext(os.path.basename(campo.name))[0] + extension
        campo.save(nombre, ContentFile(buffer.getvalue()), save=False)
    except Exception:
        try:
            campo.file.seek(0)
        except Exception:
            pass

class Noticia(models.Model):
    categoria = models.CharField(max_length=50, help_text="Ej: Preinscripciones, Egresados")
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, editable=True)
    resumen = models.TextField(
        blank=True,
        help_text="Texto corto para la tarjeta de la home (1 o 2 líneas)"
    )
    texto = models.TextField(help_text="Contenido completo de la noticia")
    autor = models.CharField(max_length=100, blank=True, default='Secretaría IES Trancas')
    fecha_publicacion = models.DateField()
    destacada = models.BooleanField(
        default=False,
        help_text="Marcar para que aparezca primero en la home"
    )
    imagen = models.ImageField(
        upload_to='imagenes/noticias/', blank=True, null=True,
        help_text="Imagen de la noticia (se reduce automáticamente a 1600 px)"
    )

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('detalle_noticia', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Noticia, self.titulo, self, 200)
        optimizar_imagen(self.imagen)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-destacada', '-fecha_publicacion']

class Carrera(models.Model):
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la carrera")
    slug = models.SlugField(max_length=200, unique=True, blank=True, editable=True)
    descripcion = models.TextField(verbose_name="descripcion breve")
    perfil_egreso = models.TextField(blank=True, help_text="perfil del egresado")
    duracion = models.CharField(max_length=50, help_text="Ej: 3 años")
    materias = models.TextField(help_text="Lista de materias separadas por comas")
    resolucion_pdf = models.FileField(upload_to='pdfs/resoluciones/', blank=True, null=True, help_text="Resolución del Ministerio (PDF)")
    plan_estudios_pdf = models.FileField(upload_to='pdfs/planes_estudio/', blank=True, null=True, help_text="Plan de estudios completo con todas las materias (PDF)")
    imagen = models.ImageField(
        upload_to='imagenes/carreras/', blank=True, null=True,
        help_text="Imagen de la carrera (se reduce automáticamente a 1600 px)"
    )

    tipo_grado = models.CharField(
        max_length=100,
        default='Técnico Superior',
        verbose_name="Grado otorgado",
        help_text="Ej: Técnico Superior, Profesor/a de Educación Secundaria en Informática, etc."
    )
    modalidad = models.CharField(
        max_length=50,
        default='Presencial',
        help_text="Ej: Presencial, Virtual, Semipresencial"
    )
    ubicacion = models.CharField(
        max_length=100,
        default='Trancas, Tucumán'
    )

    informacion_adicional = models.TextField(
        blank=True,
        help_text="Horarios, beneficios, becas y otra información útil"
    )
    color_tematico = models.CharField(
        max_length=7, default='#003366',
        help_text="Color hexadecimal (ej: #003366)"
    )
    salidas_laborales = models.TextField(
        blank=True, help_text="Una salida laboral por línea"
    )
    convenios = models.TextField(
        blank=True, help_text="Una institución por línea"
    )
    inscripciones = models.TextField(
        blank=True,
        help_text="Fechas, requisitos, documentación y pasos para inscribirse a esta carrera"
    )


    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('detalle_carrera', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slug_unico(Carrera, self.nombre, self, 200)
        optimizar_imagen(self.imagen)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['nombre']


class Autoridad(models.Model):
    iniciales = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Autoridad'
        verbose_name_plural = 'Autoridades'


class Consulta(models.Model):

    MOTIVO_CHOICES = [
        ('general', 'Consulta General'),
        ('inscripcion', 'Inscripción'),
        ('documentacion', 'Documentación'),
        ('otro', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('respondida', 'Respondida'),
        ('archivada', 'Archivada'),
    ]

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    mensaje = models.TextField(max_length=2000)  
    fecha_envio = models.DateTimeField(auto_now_add=True) 
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    notas_internas = models.TextField(
        "Notas internas", blank=True,
        help_text="Solo las ve el personal en el admin. No se muestran en el sitio"
    )

    def __str__(self):
        return f"Consulta de {self.nombre}"

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha_envio']


class ConfigInstitucion(models.Model):
    nombre = models.CharField(max_length=200, default="IES Trancas")
    direccion = models.CharField(
        max_length=300,
        default="Av. Hipólito Yrigoyen 351, Trancas, Tucumán"
    )
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(
        blank=True,
        help_text="Si lo dejás vacío, no se muestra en el sitio"
    )
    horario = models.CharField(max_length=100, blank=True, default="Lun–Vie: 17:00 a 21:30")
    url_mapa = models.TextField(
        blank=True,
        help_text="Pegá acá solo la dirección web del mapa (la que está dentro de src en el código que da Google Maps), sin las etiquetas. Vacío = no se muestra el mapa"
    )

    stat_estudiantes = models.CharField(
        "Estudiantes", max_length=20, blank=True, default="+150",
        help_text="Dejalo vacío para ocultar este dato"
    )
    stat_docentes = models.CharField(
        "Docentes", max_length=20, blank=True, default="+30",
        help_text="Dejalo vacío para ocultar este dato"
    )
    stat_anios = models.CharField(
        "Años de historia", max_length=20, blank=True, default="+15",
        help_text="Dejalo vacío para ocultar este dato"
    )

    calendario_academico = models.FileField(
        upload_to='pdfs/calendario/', blank=True, null=True,
        help_text="Calendario académico (PDF o imagen). Si no hay archivo, el link no aparece en el sitio"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Configuración Institucional'
        verbose_name_plural = 'Configuración Institucional'