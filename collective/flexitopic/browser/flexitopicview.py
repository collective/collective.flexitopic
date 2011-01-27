from zope.interface import implements, Interface
from zope.component import getUtility

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry

from collective.flexitopic.interfaces import IFlexiTopicSettings
from collective.flexitopic import flexitopicMessageFactory as _

from utils import get_search_results, get_topic_table_fields
from utils import IDX_METADATA, get_start_end

from DateTime import DateTime

KEYWORD_DELIMITER = ':'


class IFlexiTopicView(Interface):
    """
    FlexiTopic view interface
    """


class FlexiTopicView(BrowserView):
    """
    FlexiTopic browser view
    """
    implements(IFlexiTopicView)

    add_form_data_js ='//%s'

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
            width: %(width)i,
            onSubmit: addFormData,
            height: %(height)i
            }
            );

    function addFormData() {
        var dt = $('#flexitopicsearchform').serializeArray();
        $("#flexitopicresults").flexOptions({params: dt});
        %(add_js)s;
        return true;
    };

    $('#flexitopicsearchform').submit(function (){
                $('#flexitopicresults').flexOptions({newp: 1}).flexReload();
                return false;
            }
    );


        """




    def __init__(self, context, request):
        self.context = context
        self.request = request

    table_template = ViewPageTemplateFile("table.pt")

    def render_table(self, search_results):
        """ Render results table

        @return: Resulting HTML code as Python string
        """
        return self.table_template(search_results=search_results)


    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def get_subtopics(self):
        stl = []
        if self.context.hasSubtopics():
            for sub_topic in self.context.listSubtopics():
                fields = get_topic_table_fields(sub_topic, self.portal_catalog)
                results = sub_topic.queryCatalog()
                title = sub_topic.Title()
                description = sub_topic.Description()
                text = sub_topic.getText()
                id = sub_topic.id
                stl.append({'fields': fields,
                            'results': results,
                            'title': title,
                            'description': description,
                            'text': text,
                            'size': 0,
                            'start':0,
                            'display_legend': False,
                            'id': 'topic-' + id})

        return stl


    def _get_calculate_js(self, start_date):
        js_ctemplate = '''
                calculate: function( value ){
                    var start_date = new Date('%(start)s');
                    var the_date = datesliderhelper.add_date(start_date, value);
                    return datesliderhelper.format_date(the_date);
                }'''
        return js_ctemplate % { 'start': start_date.strftime('%Y/%m/%d')}

    def _get_callback_js(self, name, start_date):
        js_cbtemplate = '''
                callback: function( value ){
                    var values = value.split(';');
                    var start_date = new Date('%(start)s');
                    var start = datesliderhelper.add_date(start_date, values[0]);
                    var end = datesliderhelper.add_date(start_date, values[1]);
                    $('#start-search-%(name)s').val(datesliderhelper.format_date(start));
                    $('#end-search-%(name)s').val(datesliderhelper.format_date(end));
                    $('#flexitopicresults').flexOptions({newp: 1}).flexReload();
                }'''
        return js_cbtemplate % { 'start': start_date.strftime('%Y/%m/%d'),
                                 'name': name
                                }


    def _sel(self, item, selected):
        if item == selected:
            return 'selected="selected"'
        else:
            return ''

    def _get_index_values(self, idx):
        items = list(self.portal_catalog.Indexes[
                idx].uniqueValues())
        selected = self.request.get(idx,None)
        items.sort()
        item_list =  [{'name': _('All'), 'value':'',
                'disabled':None,
                'selected':self._sel(None,selected)}]
        for item in items:
            item_list.append({'name': item, 'value':item,
                    'disabled': None,
                    'selected':self._sel(item,selected)})
        return item_list

    def get_table_fields(self):
        return get_topic_table_fields(self.context, self.portal_catalog)

    def get_criteria(self):
        ''' combine request with topic criteria '''
        def daterange_criterion(criterion):
            date_diff = int(end_date - start_date) + 1
            i_start = int(DateTime(startval) - start_date)
            i_end = int(DateTime(endval) - start_date)
            valrange = '%i;%i' % (i_start, i_end)
            calc_template = self._get_calculate_js(start_date)
            cb_template = self._get_callback_js(criterion.Field(),
                        start_date)
            return '''
                <span id="search-%(id)s">
                    <input type=text"
                        size="10"
                        name="start-%(name)s"
                        id="start-search-%(id)s"
                        value="%(startval)s" />
                        -
                    <input type=text"
                        size="10"
                        name="end-%(name)s"
                        id="end-search-%(id)s"
                        value="%(endval)s" />
                    <input id="slider-%(id)s"
                        type="slider"
                        style="display:none;"
                        name="range-%(name)s"
                        value="%(valrange)s" />

                    <script type="text/javascript" charset="utf-8">
                      jQuery("#slider-%(id)s").slider({
                            from: 0,
                            to: %(to)i,
                            %(calculate)s,
                            %(callback)s
                            });
                    </script>

                </span>
            ''' % { 'id': criterion.Field(),
                    'name': criterion.Field(),
                    'startval' : startval,
                    'endval': endval,
                    'valrange': valrange,
                    'to': date_diff,
                    'calculate': calc_template,
                    'callback': cb_template}


        criteria = []
        portal_atct = getToolByName(self.context,'portal_atct')
        for criterion in self.context.listCriteria():
            if criterion.meta_type in ['ATSimpleStringCriterion',
                'ATSelectionCriterion', 'ATListCriterion',
                'ATDateRangeCriterion', 'ATFriendlyDateCriteria']:
                index = portal_atct.getIndex(criterion.Field())
                criterion_field = {'id': criterion.id,
                    'description': index.description,
                    'label': index.friendlyName,
                    'field': criterion.Field(),
                    'type': criterion.meta_type,
                    }
                if criterion.meta_type=='ATSimpleStringCriterion':
                    value = self.request.get(criterion.Field(),'')
                    criterion_field['input'] = '''<input type="text"
                            size="25"
                            name="%s"
                            id="search-%s"
                            value="%s"/>''' % (criterion.Field(),
                                criterion.Field(), value)
                elif criterion.meta_type in ['ATSelectionCriterion',
                                            'ATListCriterion']:
                    options = u''
                    if criterion.Value():
                        selected = self.request.get(criterion.Field(),None)
                        if criterion.getOperator()=='or':
                            # we let the user choose from the selected
                            # values
                            if selected:
                                options = u'<option value="">All</option>'
                            else:
                                options = u'<option selected="selected" value="">All</option>'
                            idx_values = list(criterion.Value())
                            idx_values.sort()
                            for idx_value in idx_values:
                                if idx_value.find(KEYWORD_DELIMITER) > 0:
                                    idx_name=idx_value.split(KEYWORD_DELIMITER)[1]
                                else:
                                    idx_name=idx_value
                                is_selected = self._sel(idx_value,selected)
                                options += u'<option value="%(value)s" %(selected)s >%(name)s</option>' % {
                                    'value': idx_value,
                                    'selected': is_selected,
                                    'name': idx_name}
                            criterion_field['input'] = '''
                                    <select id="%s" name="%s">
                                    %s
                                    </select>''' % ( criterion.Field(),
                                        criterion.Field(), options)

                        else:
                            # we let the user choose from all possible
                            # values minus the selected ones (as they will
                            # be added (AND) to the search anyway)
                            idx_values = self._get_index_values(criterion.Field())
                            for idx_value in idx_values:
                                if idx_value['value'] in criterion.Value():
                                    continue
                                else:
                                    options += u'<option value="%(value)s" %(selected)s >%(name)s</option>' % idx_value
                            criterion_field['input'] = '''
                                <select id="%s" name="%s">
                                %s
                                </select>''' % ( criterion.Field(),
                                    criterion.Field(), options)
                    else:
                        # if nothing is selected to search we assume
                        # that we should present a selection with all
                        # posible values
                        idx_values = self._get_index_values(criterion.Field())
                        for idx_value in idx_values:
                            options += u'<option value="%(value)s" %(selected)s >%(name)s</option>' % idx_value
                        criterion_field['input'] = '''
                            <select id="%s" name="%s">
                            %s
                            </select>''' % ( criterion.Field(),
                                criterion.Field(), options)
                elif criterion.meta_type in ['ATDateRangeCriterion',
                                            'ATFriendlyDateCriteria']:
                    # convert freindly date criteria into date ranges
                    # so we can display a slider to drill down inside
                    # the range
                    start_date, end_date = get_start_end(self, criterion,
                                                self.portal_catalog)
                    startval = self.request.get('start-' + criterion.Field(),
                            start_date.strftime('%Y/%m/%d'))
                    endval = self.request.get('end-' + criterion.Field(),
                            end_date.strftime('%Y/%m/%d'))

                    criterion_field['input'] = daterange_criterion(criterion)
                else:
                    criterion_field['input'] = None
                criteria.append(criterion_field)
        return criteria


    def search_results(self):
        results = get_search_results(self)
        results['fields'] = self.get_table_fields()
        results['id'] = "flexitopicresults"
        results['display_legend'] = (results['num_results'] > 0)
        return results

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
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFlexiTopicSettings)
        width=settings.flexitopic_width
        height=settings.flexitopic_height
        field_width=int(width/len(fields))
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
        add_form_data_js = self.add_form_data_js % self.context.absolute_url()
        if items_ppage==0:
            items_ppage = 15
        js = self.js_template % {
                'url':url,
                'col_model': ', '.join(tl),
                'sort': sort,
                'title': table_name,
                'items_ppage': items_ppage,
                'add_js': add_form_data_js,
                'width': width,
                'height': height,
            }
        return js

