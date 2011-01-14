from zope.interface import implements, Interface
from zope.viewlet.interfaces import IViewlet
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets import common as base

from collective.flexitopic import flexitopicMessageFactory as _

from utils import IDX_METADATA, COLUMN_WIDTH, get_topic_table_fields

class IFlexiTopicJsView(Interface):
    """
    FlexiTopicJs view interface
    """



class FlexiTopicJsView(BrowserView): #base.ViewletBase):
    """
    FlexiTopicJs browser view
    """
    #implements(IFlexiTopicJsView)
    implements(IViewlet)

    js_template = """
 $(document).ready(function() {
   $('#flexitopicsearchform').find('select').each(function(i) {
     $(this).change(function( objEvent ){
         $('#flexitopicresults').flexOptions({newp: 1}).flexReload();
        }) ;
   });
 });

    $("#flexitopicresults").flexigrid
            (
            {
            url: '%(url)s',
            dataType: 'json',
            colModel : [
                %(col_model)s
                ],
            %(sort)s
            usepager: true,
            title: '%(title)s',
            useRp: true,
            rp: %(items_ppage)i,
            showTableToggleBtn: true,
            width: 900,
            onSubmit: addFormData,
            height: 200
            }
            );

    function addFormData() {
        var dt = $('#flexitopicsearchform').serializeArray();
        $("#flexitopicresults").flexOptions({params: dt});
        return true;
    }

$('#flexitopicsearchform').submit
(
    function ()
        {
            $('#flexitopicresults').flexOptions({newp: 1}).flexReload();
            return false;
        }
);


        """

    def __init__(self, context, request, view, manager):
        self.context = context
        self.request = request
        self.js =''
        self.manager = manager
        self.view = view

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def get_js(self):
        """{display: 'Title', name : 'Title', width : 220, sortable : true, align: 'left'}"""
        def is_sortable(sortname):
            if sortname in IDX_METADATA.keys():
                return True
            elif sortname in self.portal_catalog.Indexes.keys():
                if self.portal_catalog.Indexes[sortname].meta_type in [
                        'FieldIndex', 'DateIndex', 'KeywordIndex']:
                    return True
            return False

        fields = get_topic_table_fields(self.context, self.portal_catalog)
        width=900
        field_width=int(900/len(fields))
        t = "{display: '%s', name : '%s', width : %i, sortable : %s, align: 'left'}"
        tl = []
        for field in fields:
            if is_sortable(field['name']):
                sortable='true'
            else:
                sortable='false'
            tl.append( t % (field['label'], field['name'], field_width, sortable))
        sort = ''
        for criterion in self.context.listCriteria():
            if criterion.meta_type =='ATSortCriterion':
                sortname = criterion.getCriteriaItems()[0][1]
                sortorder = 'asc'
                if len(criterion.getCriteriaItems())==2:
                    if criterion.getCriteriaItems()[1][1] =='reverse':
                        sortorder = 'desc'
                sort = "sortname: '%s', sortorder: '%s'," % (
                            sortname, sortorder)
        table_name = self.context.Title()
        url = self.context.absolute_url() + '/@@flexijson_view'
        items_ppage = self.context.getLimitNumber()
        if items_ppage==0:
            items_ppage = 15
        js = self.js_template % {
                'url':url,
                'col_model': ', '.join(tl),
                'sort': sort,
                'title': table_name,
                'items_ppage': items_ppage

            }
        return js
