"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'devcoop.menu.CustomMenu'
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from admin_tools.menu import items, Menu


class CustomMenu(Menu):
    """
    Custom Menu for devcoop admin site.
    """

    def init_with_context(self, context):

        is_superuser = context['request'].user.is_superuser

        self.children = []

        if is_superuser:
            self.children.append(
                items.MenuItem(_('Thesaurus'), '#', icon='icon-coop icon-rdf icon-white', children=[
                    items.MenuItem(_('Location categories'), '/admin/coop_geo/locationcategory/'),
                    items.MenuItem(_('Person categories'), '/admin/coop_local/personcategory/'),
                    items.MenuItem(_('Customer targets'), '/admin/coop_local/clienttarget/'),
                    items.MenuItem(_('Agreements IAE'), '/admin/coop_local/agreementiae/'),
                    items.MenuItem(_('Guaranties'), '/admin/coop_local/guaranty/'),
                    items.MenuItem(_('Tags'), '/admin/coop_local/tag/'),
                    items.MenuItem(_('Activity nomenclature'), '/admin/coop_local/activitynomenclature/'),
                    items.MenuItem(_('Roles'), '/admin/coop_local/role/'),
                    items.MenuItem(_('Legal statuses'), '/admin/coop_local/legalstatus/'),
                    items.MenuItem(_('Themes'), '/admin/coop_local/transversetheme/'),
                    items.MenuItem(_('Document types'), '/admin/coop_local/documenttype/'),
                    items.MenuItem(_('ESS categories'), '/admin/coop_local/organizationcategory/'),
                    items.MenuItem(_('IAE categories'), '/admin/coop_local/categoryiae/'),
                ])
            )

        if is_superuser:
            self.children.append(
                items.MenuItem(_('Django'), '#', icon='icon-coop icon-django icon-white', children=[
                    items.MenuItem(_('Users'), '/admin/auth/user/'),
                    items.MenuItem(_('Groups'), '/admin/auth/group/'),
                    items.MenuItem(_('Sites'), '/admin/sites/site/'),
                    items.MenuItem(_('Sites aliases'), '/admin/multisite/alias/'),
                ])
            )

        self.children.append(
            items.MenuItem(_('Network'), '#', icon='icon-coop icon-group icon-white', children=[
                items.MenuItem(_('Directory'), '#', icon='icon-home', children=[
                    items.MenuItem(_('Organizations'), '/admin/coop_local/organization/'),
                    items.MenuItem(_('Persons'), '/admin/coop_local/person/'),
                ]),
                items.MenuItem(_('Cartography'), '#', icon='icon-map-marker', children=[
                    items.MenuItem(_('Locations'), '/admin/coop_local/location/'),
                    items.MenuItem(_('Areas'), '/admin/coop_local/area/'),
                ]),
            ])
        )
