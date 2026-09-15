from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Noticia, Carrera, Autoridad, Consulta, ConfigInstitucion
import json

def index(request):
    """
    Vista que muestra la página principal (index.html)
    """
    return render(request, 'core/index.html')

def api_noticias(request):
    """
    Vista API que devuelve todas las noticias en formato JSON.
    """
    # 1. Obtener todas las noticias de la BD, ordenadas por fecha (más nuevas primero)
    noticias_db = Noticia.objects.all().order_by('-fecha_publicacion')
    
    # 2. Convertir la lista de objetos de Django a una lista de diccionarios
    #    (Esto es lo que tu JS necesita para renderizar)
    noticias_json = []
    for noticia in noticias_db:
        # Formateamos la fecha para que coincida con el formato que usás en tu JS
        # Ej: "15 de noviembre, 2026"
        fecha_str = noticia.fecha_publicacion.strftime("%d de %B, %Y")
        
        noticia_data = {
            "id": noticia.id, # type: ignore
            "categoria": noticia.categoria,
            "titulo": noticia.titulo,
            "texto": noticia.texto,
            "fecha": fecha_str,
            "imagen": noticia.imagen  # Aquí viene la ruta 'imagenes/...'
        }
        noticias_json.append(noticia_data)
    
    # 3. Devolver como JSON
    return JsonResponse(noticias_json, safe=False)


def api_carreras(request):
    """
    Vista API que devuelve todas las carreras en formato JSON.
    """
    # 1. Obtener todas las carreras
    carreras_db = Carrera.objects.all()
    
    # 2. Convertir a lista de diccionarios
    carreras_json = []
    for carrera in carreras_db:
        # Separamos las materias por coma
        materias_list = carrera.materias.split(',')

        slug = carrera.slug if carrera.slug else ''

        carrera_data = {
            'id': carrera.id, # type: ignore
            'nombre': carrera.nombre,
            'slug': slug,
            'descripcion': carrera.descripcion,
            'duracion': carrera.duracion,
            'materias': materias_list,
            # Si no tenés campo imagen en el modelo, usamos un default
            'imagen': getattr(carrera, 'imagen', 'imagenes/default_carrera.jpg')
        }
        carreras_json.append(carrera_data)
    
    return JsonResponse(carreras_json, safe=False)

def detalle_carrera(request, slug):
    """
    Vista para mostrar el detalle de una carrera específica usando slug.
    """
    carrera = get_object_or_404(Carrera, slug=slug)

        # Separamos las materias por coma y limpiamos espacios en blanco
    materias_list = [m.strip() for m in carrera.materias.split(',') if m.strip()]

    CANTIDAD_PREVIEW = 6
    materias_preview = materias_list[:CANTIDAD_PREVIEW]
    materias_restantes = max(len(materias_list) - CANTIDAD_PREVIEW, 0)
    
    context = {
        'carrera': carrera,
        'materias_list': materias_list,
        'materias_preview': materias_preview,
        'materias_restantes': materias_restantes,
    }
    
    return render(request, 'core/detalle_carrera.html', context)


def api_autoridades(request):
    """
    Vista API que devuelve todas las autoridades en formato JSON.
    """
    # 1. Obtener todas las autoridades (opcional: ordenar por cargo o nombre)
    autoridades_db = Autoridad.objects.all().order_by('cargo')
    
    # 2. Convertir a lista de diccionarios
    autoridades_json = []
    for autoridad in autoridades_db:
        autoridad_data = {
            'id': autoridad.id, # type: ignore
            'iniciales': autoridad.iniciales,
            'nombre': autoridad.nombre,
            'cargo': autoridad.cargo
        }
        autoridades_json.append(autoridad_data)
    
    return JsonResponse(autoridades_json, safe=False)


def api_contacto(request):
    """
    Vista API para recibir consultas del formulario.
    Solo acepta métodos POST.
    """
    if request.method == 'POST':
        # 1. Leer los datos JSON enviados por el JS
        try:
            datos = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

        # 2. Validar campos obligatorios
        if not datos.get('nombre') or not datos.get('email') or not datos.get('mensaje'):
            return JsonResponse({'ok': False, 'error': 'Faltan campos obligatorios'}, status=400)

        # 3. Guardar en la base de datos
        consulta = Consulta.objects.create(
            nombre=datos['nombre'],
            email=datos['email'],
            motivo=datos.get('motivo', 'otro'), # Si no envía motivo, pone 'otro' por defecto
            mensaje=datos['mensaje']
        )

        # 4. Responder éxito
        return JsonResponse({'ok': True, 'mensaje': 'Consulta enviada correctamente'})

    # Si intentan entrar con GET, devolver error o redirigir
    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


def api_config(request):
    """
    Devuelve la configuración de la institución (incluye la URL del mapa).
    """
    config = ConfigInstitucion.objects.first()
    
    if config:
        return JsonResponse({
            'nombre': config.nombre,
            'direccion': config.direccion,
            'url_mapa': config.url_mapa,
            'telefono': config.telefono,
            'email': config.email,
            'horario': config.horario
        })
    
    return JsonResponse({'error': 'No hay configuración'}, status=404)