def my_organization(request):
    if not request.user:
        return {}
    try:
        person = request.user.get_profile()
    except:
        return {}
    return {'my_organization': person.my_organization()}
