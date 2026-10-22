"""
    python manage.py test
"""
import json
import shutil
import tempfile
from datetime import date
from io import BytesIO
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Autoridad, Carrera, ConfigInstitucion, Consulta, Noticia

MEDIA_TEMPORAL = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)


def imagen_de_prueba(ancho=3000, alto=2000, nombre='foto.jpg'):
    buffer = BytesIO()
    Image.new('RGB', (ancho, alto), (200, 30, 30)).save(buffer, 'JPEG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/jpeg')


def crear_noticia(titulo='Noticia de prueba', **extra):
    datos = {
        'categoria': 'General', 'titulo': titulo,
        'texto': 'Texto de la noticia', 'fecha_publicacion': date(2026, 10, 1),
    }
    datos.update(extra)
    return Noticia.objects.create(**datos)


def crear_carrera(nombre='Tecnicatura de prueba', **extra):
    datos = {
        'nombre': nombre, 'descripcion': 'Descripción breve',
        'duracion': '3 años', 'materias': 'Matemática, Programación, Redes',
    }
    datos.update(extra)
    return Carrera.objects.create(**datos)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class PaginasPublicasTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_home_carga(self):
        self.assertEqual(self.client.get(reverse('index')).status_code, 200)

    def test_home_muestra_noticias_carreras_y_autoridades(self):
        crear_noticia('Inscripciones abiertas')
        crear_carrera('Tecnicatura en Redes')
        Autoridad.objects.create(iniciales='AB', nombre='Ana Benítez', cargo='Rectora')
        html = self.client.get(reverse('index')).content.decode()
        for texto in ['Inscripciones abiertas', 'Tecnicatura en Redes', 'Ana Benítez']:
            self.assertIn(texto, html)

    def test_home_sin_datos_no_falla(self):
        html = self.client.get(reverse('index')).content.decode()
        self.assertIn('Todavía no hay noticias', html)

    def test_home_limita_noticias_y_ofrece_ver_todas(self):
        for i in range(8):
            crear_noticia(f'Noticia número {i}')
        html = self.client.get(reverse('index')).content.decode()
        self.assertEqual(html.count('class="noticia-card"'), 6)
        self.assertIn(reverse('lista_noticias'), html)

    def test_home_no_ofrece_ver_todas_si_hay_pocas(self):
        for i in range(3):
            crear_noticia(f'Noticia número {i}')
        html = self.client.get(reverse('index')).content.decode()
        self.assertNotIn('Ver todas las noticias', html)

    def test_noticia_destacada_va_primero(self):
        crear_noticia('Vieja normal', fecha_publicacion=date(2026, 1, 1))
        crear_noticia('Nueva normal', fecha_publicacion=date(2026, 9, 1))
        crear_noticia('Destacada vieja', fecha_publicacion=date(2025, 1, 1), destacada=True)
        html = self.client.get(reverse('index')).content.decode()
        self.assertLess(html.index('Destacada vieja'), html.index('Nueva normal'))

    def test_detalle_de_noticia_con_etiquetas_para_compartir(self):
        n = crear_noticia('Gran noticia', resumen='Resumen de la gran noticia')
        r = self.client.get(n.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn('property="og:title" content="Gran noticia"', html)
        self.assertIn('Resumen de la gran noticia', html)

    def test_detalle_de_carrera(self):
        c = crear_carrera('Profesorado de Informática', inscripciones='Del 1 al 28 de febrero')
        html = self.client.get(c.get_absolute_url()).content.decode()
        self.assertIn('Profesorado de Informática', html)
        self.assertIn('Del 1 al 28 de febrero', html)
        self.assertIn('Consulta sobre esta carrera', html)  

    def test_noticia_o_carrera_inexistente_da_404(self):
        self.assertEqual(self.client.get('/noticias/no-existe/').status_code, 404)
        self.assertEqual(self.client.get('/carreras/no-existe/').status_code, 404)

    def test_pagina_404_tiene_el_diseno_del_sitio(self):
        r = self.client.get('/esto-no-existe/')
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'No encontramos esta página', status_code=404)

    def test_listado_de_noticias_pagina_de_a_9(self):
        for i in range(12):
            crear_noticia(f'Noticia {i:02d}', fecha_publicacion=date(2026, 1, i + 1))
        url = reverse('lista_noticias')
        p1 = self.client.get(url).content.decode()
        p2 = self.client.get(url + '?page=2').content.decode()
        self.assertEqual(p1.count('class="noticia-card"'), 9)
        self.assertEqual(p2.count('class="noticia-card"'), 3)
        self.assertIn('Página 1 de 2', p1)

    def test_listado_con_numero_de_pagina_invalido_no_falla(self):
        for i in range(12):
            crear_noticia(f'Noticia {i:02d}')
        url = reverse('lista_noticias')
        for param in ['?page=999', '?page=abc', '?page=-3', '?page=']:
            self.assertEqual(self.client.get(url + param).status_code, 200, param)

    def test_sitemap_lista_las_paginas(self):
        n = crear_noticia('Para el mapa')
        c = crear_carrera('Carrera para el mapa')
        r = self.client.get('/sitemap.xml')
        self.assertEqual(r.status_code, 200)
        xml = r.content.decode()
        for ruta in [n.get_absolute_url(), c.get_absolute_url(), reverse('lista_noticias')]:
            self.assertIn(ruta, xml)

    def test_robots_bloquea_admin_y_apunta_al_sitemap(self):
        texto = self.client.get('/robots.txt').content.decode()
        self.assertIn('Disallow: /admin/', texto)
        self.assertIn('/sitemap.xml', texto)

    def test_accesibilidad_basica_en_la_home(self):
        html = self.client.get(reverse('index')).content.decode()
        self.assertIn('class="skip-link"', html)          
        self.assertIn('<main', html)                       
        self.assertIn('aria-expanded="false"', html)      
        self.assertIn('<label for="nombre"', html)     
        self.assertIn('<label for="mensaje"', html)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class ModelosTests(TestCase):
    def test_titulos_repetidos_generan_slugs_distintos(self):
        a, b, c = (crear_noticia('Mismo título') for _ in range(3))
        self.assertEqual(len({a.slug, b.slug, c.slug}), 3)

    def test_titulo_solo_con_simbolos_igual_tiene_slug(self):
        n = crear_noticia('¡¿?!')
        self.assertTrue(n.slug)

    def test_imagen_grande_se_reduce(self):
        n = crear_noticia('Con foto', imagen=imagen_de_prueba(3000, 2000))
        with Image.open(n.imagen.path) as img:
            self.assertLessEqual(max(img.size), 1600)

    def test_imagen_chica_no_se_agranda(self):
        n = crear_noticia('Con foto chica', imagen=imagen_de_prueba(800, 600))
        with Image.open(n.imagen.path) as img:
            self.assertEqual(img.size, (800, 600))


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class ConfigInstitucionTests(TestCase):
    def test_sin_configuracion_no_muestra_email_ni_calendario(self):
        html = self.client.get(reverse('index')).content.decode()
        self.assertNotIn('mailto:', html)
        self.assertNotIn('Calendario académico', html)

    def test_con_configuracion_muestra_los_datos(self):
        ConfigInstitucion.objects.create(
            email='contacto@ejemplo.com', telefono='381-555-0000',
            calendario_academico=SimpleUploadedFile('cal.pdf', b'%PDF-1.4', 'application/pdf'),
        )
        html = self.client.get(reverse('index')).content.decode()
        self.assertIn('mailto:contacto@ejemplo.com', html)
        self.assertIn('381-555-0000', html)
        self.assertIn('Calendario académico', html)

    def test_estadisticas_vacias_se_ocultan(self):
        ConfigInstitucion.objects.create(stat_estudiantes='', stat_docentes='+40', stat_anios='')
        html = self.client.get(reverse('index')).content.decode()
        self.assertNotIn('>Estudiantes<', html)
        self.assertIn('+40', html)


class ContactoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('api_contacto')

    def enviar(self, **cambios):
        datos = {
            'nombre': 'Ana', 'email': 'ana@ejemplo.com', 'motivo': 'general',
            'mensaje': 'Quisiera saber las fechas de inscripción.',
            'web': '', 'segundos': 30,
        }
        datos.update(cambios)
        return self.client.post(self.url, data=json.dumps(datos), content_type='application/json')

    def test_consulta_valida_se_guarda(self):
        r = self.enviar()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        c = Consulta.objects.get()
        self.assertEqual(c.estado, 'pendiente')
        self.assertEqual(c.nombre, 'Ana')

    def test_solo_acepta_post(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_json_invalido(self):
        r = self.client.post(self.url, data='esto no es json', content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_faltan_campos(self):
        self.assertEqual(self.enviar(nombre='').status_code, 400)
        self.assertEqual(self.enviar(mensaje='   ').status_code, 400)
        self.assertEqual(Consulta.objects.count(), 0)

    def test_email_invalido(self):
        self.assertEqual(self.enviar(email='no-es-un-mail').status_code, 400)

    def test_mensaje_demasiado_largo(self):
        self.assertEqual(self.enviar(mensaje='x' * 2001).status_code, 400)

    def test_motivo_desconocido_se_guarda_como_otro(self):
        self.enviar(motivo='Consulta sobre una carrera larguísima')
        self.assertEqual(Consulta.objects.get().motivo, 'otro')

    def test_campo_trampa_lleno_no_se_guarda_pero_responde_ok(self):
        r = self.enviar(web='http://spam.example')
        self.assertTrue(r.json()['ok'])  # el bot cree que funcionó
        self.assertEqual(Consulta.objects.count(), 0)

    def test_envio_demasiado_rapido_no_se_guarda(self):
        r = self.enviar(segundos=1)
        self.assertTrue(r.json()['ok'])
        self.assertEqual(Consulta.objects.count(), 0)

    def test_navegador_con_js_viejo_igual_puede_enviar(self):
        datos = {'nombre': 'Luis', 'email': 'luis@ejemplo.com', 'mensaje': 'Hola'}
        r = self.client.post(self.url, data=json.dumps(datos), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Consulta.objects.count(), 1)

    def test_limite_de_5_consultas_por_ip(self):
        for _ in range(5):
            self.assertEqual(self.enviar().status_code, 200)
        self.assertEqual(self.enviar().status_code, 429)
        self.assertEqual(Consulta.objects.count(), 5)

    def test_el_limite_es_por_persona_no_global(self):
        for _ in range(5):
            self.enviar()
        r = self.client.post(
            self.url, content_type='application/json', HTTP_CF_CONNECTING_IP='9.9.9.9',
            data=json.dumps({'nombre': 'Otra', 'email': 'otra@ejemplo.com', 'mensaje': 'Hola', 'segundos': 20}),
        )
        self.assertEqual(r.status_code, 200)


class AdminTests(TestCase):
    def setUp(self):
        User.objects.create_superuser('admin', 'admin@ejemplo.com', 'clave-de-prueba')
        self.client.login(username='admin', password='clave-de-prueba')

    def test_listado_de_consultas(self):
        Consulta.objects.create(nombre='Ana', email='a@x.com', motivo='general', mensaje='Hola')
        r = self.client.get(reverse('admin:core_consulta_changelist'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Marcar como respondidas')

    def test_accion_marcar_como_respondida(self):
        c = Consulta.objects.create(nombre='Ana', email='a@x.com', motivo='general', mensaje='Hola')
        self.client.post(reverse('admin:core_consulta_changelist'),
                         {'action': 'marcar_respondida', '_selected_action': [c.pk]})
        c.refresh_from_db()
        self.assertEqual(c.estado, 'respondida')

    def test_no_se_pueden_crear_consultas_a_mano(self):
        self.assertEqual(self.client.get(reverse('admin:core_consulta_add')).status_code, 403)

    def test_configuracion_es_un_unico_registro(self):
        self.assertEqual(self.client.get(reverse('admin:core_configinstitucion_add')).status_code, 200)
        ConfigInstitucion.objects.create()
        self.assertEqual(self.client.get(reverse('admin:core_configinstitucion_add')).status_code, 403)

    def test_formulario_de_configuracion_muestra_todas_las_secciones(self):
        cfg = ConfigInstitucion.objects.create()
        html = self.client.get(reverse('admin:core_configinstitucion_change', args=[cfg.pk])).content.decode()
        for texto in ['name="url_mapa"', 'name="calendario_academico"', 'name="stat_estudiantes"']:
            self.assertIn(texto, html)
        self.assertNotIn('<iframe', html)  