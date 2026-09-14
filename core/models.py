from django.db import models

# Create your models here.
# 1. MODELO DE NOTICIAS
class Noticia(models.Model):
    categoria = models.CharField(max_length=50, help_text="Ej: Preinscripciones, Egresados")
    titulo = models.CharField(max_length=200)
    texto = models.TextField()
    fecha_publicacion = models.DateField()
    # Usamos CharField para la imagen por ahora (guardaremos la ruta), 
    # si querés subir archivos reales, luego cambiamos a ImageField
    imagen = models.CharField(max_length=255, default='imagenes/logo.png')

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
        ordering = ['-fecha_publicacion']

# 2. MODELO DE CARRERAS
class Carrera(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    duracion = models.CharField(max_length=50, help_text="Ej: 3 años")
    # Guardamos las materias como texto separado por comas para simplificar
    materias = models.TextField(help_text="Lista de materias separadas por comas")
    imagen = models.CharField(max_length=255, default='imagenes/default_carrera.jpg')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'


# 3. MODELO DE AUTORIDADES
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
    # Opciones para el motivo (validación automática)
    MOTIVO_CHOICES = [
        ('general', 'Consulta General'),
        ('inscripcion', 'Inscripción'),
        ('documentacion', 'Documentación'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    mensaje = models.TextField(max_length=2000)  # Límite de 2000 caracteres
    fecha_envio = models.DateTimeField(auto_now_add=True) # Se llena solo al crear
    estado = models.CharField(max_length=10, default='pendiente')

    def __str__(self):
        return f"Consulta de {self.nombre}"

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-fecha_envio']


class ConfigInstitucion(models.Model):
    nombre = models.CharField(max_length=200, default="IES Trancas")
    direccion = models.CharField(max_length=300)
    # Aquí guardamos la URL de embed de Google Maps
    url_mapa = models.TextField(help_text="Pegá acá la URL del iframe de Google Maps")
    telefono = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    horario = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Configuración Institucional'
        verbose_name_plural = 'Configuración Institucional'