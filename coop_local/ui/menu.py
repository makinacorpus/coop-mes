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
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children = [
            #items.MenuItem(_('Dashboard'), reverse('admin:index')),
            #items.Bookmarks('Favoris'),

            #items.MenuItem(_('Navigation tree'), '/admin/coop_local/navtree/1/', icon='icon-list-alt icon-white'),

            #items.MenuItem(_('Articles'), '/admin/coop_local/article/', icon='icon-pencil icon-white'),

            #items.MenuItem(_('CMS'), '#', icon='icon-cog icon-white',
                #children=[

                    #items.MenuItem(_('Content'), '#', icon='icon-file', children=[
                        #items.MenuItem(_('Article categories'), '/admin/coop_cms/articlecategory/'),
                        #items.MenuItem(_('Documents'), '/admin/coop_cms/document/'),
                        #items.MenuItem(_('Images'), '/admin/coop_cms/image/'),
                        #items.MenuItem(_('Newsletters'), '/admin/coop_cms/newsletter/'),
                        #items.MenuItem(_('Comments'), '/admin/comments/comment/'),
                        #items.MenuItem(_('Forms'), '/admin/forms/form/'),
                        #items.MenuItem(_('Preferences'), '/admin/coop_local/siteprefs/'),

                        #]),

                    ## RSS Sync menu gets inserted here if installed (see above)

                    items.MenuItem(_('Thesaurus'), '#', icon='icon-coop icon-rdf icon-white', children=[
                        items.MenuItem(_('Location categories'), '/admin/coop_geo/locationcategory/'),
                        items.MenuItem(_('Person categories'), '/admin/coop_local/personcategory/'),
                        items.MenuItem(_('Client targets'), '/admin/coop_local/clienttarget/'),
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
                        ##items.MenuItem(_('Tag categories'), '/admin/coop_tag/tagcategory/'),
                        #items.MenuItem(_('Tag trees'), '/admin/coop_local/navtree/'),
                        ]),

                    items.MenuItem(_('Django'), '#', icon='icon-coop icon-django icon-white', children=[
                        items.MenuItem(_('Users'), '/admin/auth/user/'),
                        items.MenuItem(_('Sites'), '/admin/sites/site/'),
                        items.MenuItem(_('Sites aliases'), '/admin/multisite/alias/'),
                        ]),
                #]
            #),


            # Agenda menu inserted here if coop.agenda installed

            items.MenuItem(_('Network'), '#', icon='icon-coop icon-group icon-white',
                children=[

                    items.MenuItem(_('Directory'), '#', icon='icon-home', children=[
                        items.MenuItem(_('Providers'), '/admin/coop_local/provider/'),
                        items.MenuItem(_('Clients'), '/admin/coop_local/client/'),
                        items.MenuItem(_('Network'), '/admin/coop_local/network/'),
                        items.MenuItem(_('Persons'), '/admin/coop_local/person/'),
                        ]),

                    #items.MenuItem(_('Exchanges'), '#', icon='icon-random', children=[
                        #items.MenuItem(_('Exchanges'), '/admin/coop_local/exchange/'),
                        #items.MenuItem(_('Exchange methods'), '/admin/coop_local/exchangemethod/'),
                        #]),

                    items.MenuItem(_('Cartography'), '#', icon='icon-map-marker', children=[
                        items.MenuItem(_('Locations'), '/admin/coop_local/location/'),
                        items.MenuItem(_('Areas'), '/admin/coop_local/area/'),
                        # create my map !
                        ]),

                    #items.MenuItem(_('RDF settings'), '#', icon='icon-coop icon-rdf', children=[
                        #items.MenuItem(_('URI redirection'), '/admin/uriredirect/'),
                        ## webid
                        #]),


                ]
            ),



        ]

        #if 'coop_cms.apps.rss_sync' in  settings.INSTALLED_APPS:
            #self.children[2].children.insert(1,

                    #items.MenuItem(_('RSS'), '#', icon='icon-coop icon-rss', children=[
                        #items.MenuItem(_('RSS items'), '/admin/rss_sync/rssitem/'),
                        #items.MenuItem(_('RSS sources'), '/admin/rss_sync/rsssource/'),
                        #])
                    #)

        #if 'coop.agenda' in settings.INSTALLED_APPS:
            #self.children.insert(2,
                #items.MenuItem(_('Agenda'), '#', icon='icon-calendar icon-white',
                    #children=[
                        #items.MenuItem(_('Events'), '/admin/coop_local/event/'),
                        #items.MenuItem(_('Calendar'), '/admin/coop_local/calendar/'),
                        #items.MenuItem(_('Event categories'), '/admin/coop_local/eventcategory/'),
                    #])
                #)

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(CustomMenu, self).init_with_context(context)
