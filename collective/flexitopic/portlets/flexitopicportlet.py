from AccessControl import getSecurityManager

from zope import schema
from zope.component import getMultiAdapter, getUtility
from zope.formlib import form
from zope.interface import Interface
from zope.interface import implements

from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget
from plone.app.portlets.portlets import base
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.flexitopic import flexitopicMessageFactory as _

from zope.i18nmessageid import MessageFactory
__ = MessageFactory("plone")

class IFlexiTopicPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    # Any zope.schema fields here are to capture portlet configuration
    # information.

    header = schema.TextLine(
        title=__(u"Portlet header"),
        description=__(u"Title of the rendered portlet"),
        required=True)

    target_collection = schema.Choice(
        title=__(u"Target collection"),
        description=__(u"Find the collection which provides the items to list"),
        required=True,
        source=SearchableTextSourceBinder(
            {'portal_type': ('Topic', 'Collection')},
            default_query='path:'))

    limit = schema.Int(
        title=__(u"Limit"),
        description=__(u"Specify the maximum number of items to show in the "
                      u"portlet. Leave this blank to show all items."),
        required=False)


    show_more = schema.Bool(
        title=__(u"Show more... link"),
        description=__(u"If enabled, a more... link will appear in the footer "
                      u"of the portlet, linking to the underlying "
                      u"Collection."),
        required=True,
        default=True)

    omit_border = schema.Bool(
        title=__(u"Omit portlet border"),
        description=_(u"Tick this box if you want to render the Form and Flexigrid"
            "without the standard header, border or footer."),
        required=True,
        default=False)

    flexitopic_width = schema.Int(title=_(u"Flexitopic width"),
                                  description=_(u"Width of the flexigrid table"),
                                  required=False,
                                  min=0,
                                  default=None)

    flexitopic_height = schema.Int(title=_(u"Flexitopic height"),
                                  description=_(u"Height of the flexigrid table"),
                                  required=False,
                                  min=0,
                                  default=None)

    show_form = schema.Bool(title=_("Show search form"),
                description=_(u"Uncheck if you want to hide the searchform"),
                required=False,
                default=True,)



class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IFlexiTopicPortlet)

    # Set default values for the configurable parameters here

    header = u""
    target_collection = None
    limit = None
    show_more = True
    omit_border = False
    flexitopic_width = None
    flexitopic_height = None
    show_form = True

    def __init__(self, header=u"", target_collection=None, limit=None,
                 show_more=True, omit_border=False,
                 flexitopic_width=None, flexitopic_height=None,
                 show_form = True):
        self.header = header
        self.target_collection = target_collection
        self.limit = limit
        self.show_more = show_more
        self.omit_border = omit_border
        self.flexitopic_width = flexitopic_width
        self.flexitopic_height = flexitopic_height
        self.show_form = show_form



    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"FlexiTopic")


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('flexitopicportlet.pt')

    def css_class(self):
        """Generate a CSS class from the portlet header
        """
        header = self.data.header
        if header:
            normalizer = getUtility(IIDNormalizer)
            return "portlet-flexitopic-%s" % normalizer.normalize(header)
        return "portlet-flexitopic"


    def collection_url(self):
        collection = self.collection()
        if collection is None:
            return None
        else:
            return collection.absolute_url()

    @property
    def available(self):
        """ do not show if the collection is empty """
        return len(self.results())

    @memoize
    def results(self):
        """ only used to check if the portlet is available"""
        results = []
        collection = self.collection()
        if collection is not None:
            results = collection.queryCatalog(batch=True, b_size=1)
        return results

    @memoize
    def collection(self):
        collection_path = self.data.target_collection
        if not collection_path:
            return None

        if collection_path.startswith('/'):
            collection_path = collection_path[1:]

        if not collection_path:
            return None

        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u'plone_portal_state')
        portal = portal_state.portal()
        if isinstance(collection_path, unicode):
            # restrictedTraverse accepts only strings
            collection_path = str(collection_path)

        result = portal.unrestrictedTraverse(collection_path, default=None)
        if result is not None:
            sm = getSecurityManager()
            if not sm.checkPermission('View', result):
                result = None
        return result

    def is_old_style(self):
        return self.collection().portal_type == "Topic"

    def show_table(self):
        return True

    def show_form(self):
        return self.data.show_form




class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IFlexiTopicPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

    label = _(u"Add Flexitopic Portlet")
    description = _(u""" You can search the collection with the fields
                    you provided in the topic criteria.
                    """)

    def create(self, data):
        return Assignment(**data)



class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IFlexiTopicPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

    label=_(u"Edit FlexiTopic Portlet")
    description = _(u""" You can search the collection with the fields
                    you provided in the topic criteria.
                    """)
