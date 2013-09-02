from coop_local.models import Organization

def my_organization(request):
    return {'my_organization': Organization.mine(request)}
