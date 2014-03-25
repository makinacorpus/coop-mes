from coop_local.models import Organization
from django.conf import settings

def my_organization(request):
    return {'my_organization': Organization.mine(request)}

def region_slug(request):
    return {
        'region_slug': settings.REGION_SLUG,
        'region_name': settings.REGION_NAME,
    }
