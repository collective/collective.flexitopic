from zope.interface import implements
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from interfaces import IFlexiTopicView
from utils import get_renderd_table

class FlexiTopicView(BrowserView):

    implements(IFlexiTopicView)

    __call__ = ViewPageTemplateFile('templates/flexitopicview.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()




class FlexiCollectionView(FlexiTopicView):
    """
    FlexiTopic browser view
    """
    __call__ = ViewPageTemplateFile('templates/flexicollectionview.pt')
