# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from django.contrib.auth.views import (login, logout, password_reset,
    password_reset_done, password_reset_confirm, password_reset_complete)
from .forms import AuthenticationForm, PreferencesForm
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, authenticate
from django.contrib.sites.models import get_current_site
from django.utils.http import is_safe_url
from django.http import HttpResponse, HttpResponseRedirect
from coop_local.models import Organization, Person
from django.contrib.auth.decorators import login_required
from ionyweb.page.models import Page
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from  django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.utils.text import get_text_list


# from ionyweb.website.rendering.medias import CSSMedia, JSMedia, JSAdminMedia
MEDIAS = (
    # App CSS
    # CSSMedia('page_account.css'),
    # App JS
    # JSMedia('page_account.js'),
    # Actions JSAdmin
    # JSAdminMedia('page_account_actions.js'),
    )

@login_required
def index_view(request, page_app):
    return render_view('page_account/index.html',
                       { 'object': page_app },
                       MEDIAS,
                       context_instance=RequestContext(request))


def login_view(request, page_app):

    return login(request)


def login(request, template_name='page_account/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():

            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = '/'

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    return render_view(template_name,
        context,
        MEDIAS,
        context_instance=RequestContext(request))


def logout_view(request, page_app):

    return logout(request)


def make_ionyweb_view(view, **kwargs):
    def ionyweb_view(request, page_app, **kwargs2):
        kwargs.update(kwargs2)
        response = view(request, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            return response
        response.render()
        return render_view('content.html', {'content': response.content}, (),
            context_instance=RequestContext(request))
    return ionyweb_view

password_reset_view = make_ionyweb_view(password_reset,
    template_name='page_account/password_reset_form.html',
    email_template_name='page_account/password_reset_email.html',
    post_reset_redirect='/mon-compte/p/password_reset_done/',
    from_email=Plugin_Contact.objects.all()[0].email)

password_reset_done_view = make_ionyweb_view(password_reset_done,
    template_name='page_account/password_reset_done.html')

password_reset_confirm_view = make_ionyweb_view(password_reset_confirm,
    template_name='page_account/password_reset_confirm.html',
    post_reset_redirect='/mon-compte/p/password_reset_complete/')

password_reset_complete_view = make_ionyweb_view(password_reset_complete,
    template_name='page_account/password_reset_complete.html')


@login_required
def organizations_view(request, page_app):

    try:
        person = Person.objects.get(user=request.user)
    except Person.DoesNotExist:
        raise HttpResponseForbidden('Votre compte n\'est lié à aucune organisation.')
    org = person.my_organization()
    providers = Organization.objects.filter(target__relation_type__id=2, target__source=org)
    customers = Organization.objects.filter(target__relation_type__id=6, target__source=org)
    return render_view('page_account/organizations.html',
        {'providers': providers, 'customers': customers},
        MEDIAS,
        context_instance=RequestContext(request))


@login_required
def my_calls_view(request, page_app):
    return render_view('page_account/my_calls.html',
                       {'object': page_app},
                       MEDIAS,
                       context_instance=RequestContext(request))


@login_required
def my_offers_view(request, page_app):
    return render_view('page_account/my_offers.html',
                       {'object': page_app},
                       MEDIAS,
                       context_instance=RequestContext(request))


@login_required
def my_preferences_view(request, page_app):
    try:
        person = Person.objects.get(user=request.user)
    except Person.DoesNotExist:
        raise HttpResponseForbidden('Votre compte n\'est lié à aucune organisation.')
    org = person.my_organization()
    if not org:
        return HttpResponseForbidden('Votre compte n\'est lié à aucune organisation.')
    form = PreferencesForm(request.POST if request.method == 'POST' else None, instance=org)
    if form.is_valid():
        form.save()
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Organization).pk,
            object_id       = org.pk,
            object_repr     = force_unicode(org),
            action_flag     = CHANGE,
            change_message  = u'%s modifié pour l\'appel d\'offres "%s".' % (get_text_list(form.changed_data, _('and')), force_unicode(org))
        )
        return HttpResponseRedirect('/mon-compte/')
    print form.errors
    return render_view('page_account/my_preferences.html',
                       {'object': page_app, 'form': form},
                       MEDIAS,
                       context_instance=RequestContext(request))
