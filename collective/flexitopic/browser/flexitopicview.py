from zope.interface import implements
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from interfaces import IFlexiTopicView
from utils import get_renderd_table

class FlexiTopicView(BrowserView):
    """
    FlexiTopic browser view
    """
    implements(IFlexiTopicView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def render_table(self, search_results):
        return get_renderd_table(self, search_results)

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()




