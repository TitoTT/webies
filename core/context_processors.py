from .models import ConfigInstitucion


def config_institucion(request):

    config = ConfigInstitucion.objects.first() or ConfigInstitucion()
    return {'config_institucion': config}