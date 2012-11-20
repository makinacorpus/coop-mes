"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'devcoop.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name
from django.conf import settings

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for coop-mes.
    """
    columns = 2
    title = ''
    template = 'admin_tools/coop_dashboard.html'

    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        # append a recent actions module
        self.children.append(modules.RecentActions(_('Recent Actions'), 10))
