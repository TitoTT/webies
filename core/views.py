import json
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Autoridad, Carrera, Consulta, Noticia

NOTICIAS_EN_HOME = 6      
NOTICIAS_POR_PAGINA = 9   
MATERIAS_EN_PREVIEW = 6   


LIMITE_ENVIOS = 5          
VENTANA_SEGUNDOS = 3600    
SEGUNDOS_MINIMOS = 3       

DESCRIPCION_SITIO = (
    'Instituto de Educación Superior de Trancas, Tucumán. '
    'Tecnicaturas y profesorados de nivel superior.'
)


def _resumir(texto, largo=200):
    """Texto en una sola línea y recortado, para las etiquetas meta."""
    texto = ' '.join((texto or '').split())
    if len(texto) <= largo:
        return texto
    return texto[:largo - 1].rstrip() + '…'


def _ip_cliente(request):
    """IP real de la visita. Detrás de Cloudflare viene en CF-Connecting-IP."""
    return request.META.get('HTTP_CF_CONNECTING_IP') or request.META.get('REMOTE_ADDR', 'desconocida')


@ensure_csrf_cookie
def index(request):
    """Página principal: noticias, carreras y autoridades salen directo de la base."""
    carreras = list(Carrera.objects.exclude(slug=''))
    noticias = Noticia.objects.exclude(slug='')

    context = {
        'noticias': noticias[:NOTICIAS_EN_HOME],
        'hay_mas_noticias': noticias.count() > NOTICIAS_EN_HOME,
        'carreras': carreras,
        'total_carreras': len(carreras),
        'autoridades': Autoridad.objects.order_by('cargo'),
        'meta_descripcion': DESCRIPCION_SITIO,
    }
    return render(request, 'core/home.html', context)


def lista_noticias(request):
    """Todas las noticias, de a NOTICIAS_POR_PAGINA por página."""
    noticias = Noticia.objects.exclude(slug='').order_by('-destacada', '-fecha_publicacion', '-id')
    paginador = Paginator(noticias, NOTICIAS_POR_PAGINA)
    pagina = paginador.get_page(request.GET.get('page'))  

    context = {
        'page_obj': pagina,
        'paginas': paginador.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1), # type: ignore
        'meta_titulo': 'Noticias - IES Trancas',
        'meta_descripcion': 'Novedades, avisos y comunicados del Instituto de Educación Superior de Trancas.',
    }
    return render(request, 'core/lista_noticias.html', context)


def detalle_noticia(request, slug):
    """Página individual de una noticia."""
    noticia = get_object_or_404(Noticia, slug=slug)

    otras = Noticia.objects.exclude(slug='').exclude(pk=noticia.pk)
    relacionadas = list(otras.filter(categoria=noticia.categoria)[:3])

    
    if len(relacionadas) < 3:
        faltan = 3 - len(relacionadas)
        extra = otras.exclude(pk__in=[r.pk for r in relacionadas])[:faltan]
        relacionadas += list(extra)

    context = {
        'noticia': noticia,
        'relacionadas': relacionadas,
        'meta_titulo': noticia.titulo,
        'meta_descripcion': _resumir(noticia.resumen or noticia.texto),
        'meta_imagen': noticia.imagen.url if noticia.imagen else '',
        'meta_tipo': 'article',
    }
    return render(request, 'core/detalle_noticia.html', context)


@ensure_csrf_cookie
def detalle_carrera(request, slug):
    """Página de detalle de una carrera."""
    carrera = get_object_or_404(Carrera, slug=slug)

    materias_list = [m.strip() for m in carrera.materias.split(',') if m.strip()]

    context = {
        'carrera': carrera,
        'materias_list': materias_list,
        'materias_preview': materias_list[:MATERIAS_EN_PREVIEW],
        'materias_restantes': max(len(materias_list) - MATERIAS_EN_PREVIEW, 0),
        'meta_titulo': carrera.nombre,
        'meta_descripcion': _resumir(carrera.descripcion),
        'meta_imagen': carrera.imagen.url if carrera.imagen else '',
    }
    return render(request, 'core/detalle_carrera.html', context)


def api_contacto(request):
    """Recibe consultas del formulario. Solo acepta POST."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not isinstance(datos, dict):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    # ── Anti-spam ─────────────────────────────────────────
    respuesta_falsa = JsonResponse({'ok': True, 'mensaje': 'Consulta enviada correctamente'})

    # 1) Campo trampa: está oculto para las personas, solo los bots lo completan
    if str(datos.get('web', '')).strip():
        return respuesta_falsa

    # 2) Enviado demasiado rápido: un humano no escribe un mensaje en 3 segundos
    # (si no viene el dato, por ejemplo con el JS viejo en caché, no se bloquea)
    segundos = datos.get('segundos')
    if isinstance(segundos, (int, float)) and segundos < SEGUNDOS_MINIMOS:
        return respuesta_falsa

    # 3) Límite de envíos por IP
    clave = f'contacto_envios:{_ip_cliente(request)}'
    if cache.get(clave, 0) >= LIMITE_ENVIOS:
        return JsonResponse(
            {'ok': False, 'error': 'Enviaste muchas consultas en poco tiempo. Probá de nuevo más tarde.'},
            status=429,
        )

    # ── Validación ────────────────────────────────────────
    nombre = str(datos.get('nombre', '')).strip()
    email = str(datos.get('email', '')).strip()
    mensaje = str(datos.get('mensaje', '')).strip()
    motivo = datos.get('motivo', 'otro')

    if not nombre or not email or not mensaje:
        return JsonResponse({'ok': False, 'error': 'Faltan campos obligatorios'}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'ok': False, 'error': 'El email no es válido'}, status=400)

    if len(nombre) > 100:
        return JsonResponse({'ok': False, 'error': 'El nombre es demasiado largo'}, status=400)
    if len(mensaje) > 2000:
        return JsonResponse({'ok': False, 'error': 'El mensaje supera los 2000 caracteres'}, status=400)

    # Si el motivo no es uno de los permitidos, se guarda como 'otro'
    motivos_validos = [clave_motivo for clave_motivo, _ in Consulta.MOTIVO_CHOICES]
    if motivo not in motivos_validos:
        motivo = 'otro'

    Consulta.objects.create(nombre=nombre, email=email, motivo=motivo, mensaje=mensaje)

    # Sumamos 1 al contador de esta IP (se vence solo después de la ventana)
    if not cache.add(clave, 1, VENTANA_SEGUNDOS):
        try:
            cache.incr(clave)
        except ValueError:
            cache.set(clave, 1, VENTANA_SEGUNDOS)

    return JsonResponse({'ok': True, 'mensaje': 'Consulta enviada correctamente'})


def robots_txt(request):
    """robots.txt: le dice a Google qué no indexar y dónde está el sitemap."""
    lineas = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /api/',
        '',
        f'Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lineas), content_type='text/plain')


# ── Vista previa de las páginas de error (solo con DEBUG = True) ──
def preview_404(request):
    return render(request, '404.html', status=404)


def preview_500(request):
    return render(request, '500.html', status=500)