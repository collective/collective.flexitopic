from DateTime import DateTime
from zope.component import getUtility
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.viewlets import common as base

from Products.CMFCore.utils import getToolByName

from plone.registry.interfaces import IRegistry

from collective.flexitopic.interfaces import IFlexiTopicSettings
from collective.flexitopic import flexitopicMessageFactory as _
from utils import get_search_results, get_topic_table_fields
from utils import IDX_METADATA, DATERANGE_OPERATORS
from utils import get_start_end, get_renderd_table
from utils import get_search_results_ng, get_start_end_ng

try:
    from plone.app.querystring import queryparser
    from plone.app.querystring.registryreader import QuerystringRegistryReader
except ImportError:
    pass

KEYWORD_DELIMITER = ':'
DATE_FIELD_WIDTH = 80
FG_PADDING_WIDTH = 5





class BaseViewlet(base.ViewletBase):
    ''' a common base for the viewlets used here '''

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

class AboutViewlet(BaseViewlet):
    ''' displays the description of a topic '''

class SubtopicViewlet(BaseViewlet):
    ''' displays the subtopics of a topic '''

    def render_table(self, search_results):
        return get_renderd_table(self, search_results)

    def get_subtopics(self):
        stl = []
        if self.context.hasSubtopics():
            for sub_topic in self.context.listSubtopics():
                fields = get_topic_table_fields(sub_topic, self.portal_catalog)
                results = sub_topic.queryCatalog()
                title = sub_topic.Title()
                description = sub_topic.Description()
                text = sub_topic.getText()
                size = sub_topic.getItemCount()
                id = sub_topic.id
                stl.append({'fields': fields,
                            'results': results,
                            'title': title,
                            'description': description,
                            'text': text,
                            'size': size,
                            'start':0,
                            'display_legend': False,
                            'id': 'topic-' + id})

        return stl

class FormViewlet(BaseViewlet):
    ''' displays the query form for old style collections'''

    jslider_template = u'''
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
            '''

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    def _get_calculate_js(self, start_date):
        js_ctemplate = u'''
                calculate: function( value ){
                    var start_date = new Date('%(start)s');
                    var the_date = datesliderhelper.add_date(start_date, value);
                    return datesliderhelper.format_date(the_date);
                }'''
        return js_ctemplate % { 'start': start_date.strftime('%Y/%m/%d')}

    def _get_callback_js(self, name, start_date):
        js_cbtemplate = u'''
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
            return u'selected="selected"'
        else:
            return u''

    def _get_index_values(self, idx):
        items = list(self.portal_catalog.Indexes[
                idx].uniqueValues())
        selected = self.request.get(idx,None)
        items.sort()
        item_list =  [{u'name': _(u'All'), u'value':u'',
                u'disabled':None,
                u'selected':self._sel(None,selected)}]
        for item in items:
            item_list.append({u'name': item.decode('utf-8'),
                    u'value':item.decode('utf-8'),
                    u'disabled': None,
                    u'selected':self._sel(item,selected)})
        return item_list


    def _daterange_criterion(self, field_name, start_date, form_start, end_date, form_end):
        date_diff = int(end_date - start_date) + 1
        i_start = int(DateTime(form_start) - start_date)
        i_end = int(DateTime(form_end) - start_date)
        valrange = u'%i;%i' % (i_start, i_end)
        calc_template = self._get_calculate_js(start_date)
        cb_template = self._get_callback_js(field_name,
                    start_date)
        return  self.jslider_template % {
                'id': field_name,
                'name': field_name,
                'startval' : form_start,
                'endval': form_end,
                'valrange': valrange,
                'to': date_diff,
                'calculate': calc_template,
                'callback': cb_template}

    def get_criteria(self):
        ''' combine request with topic criteria '''
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
                    criterion_field['input'] = u'''<input type="text"
                            size="25"
                            name="%s"
                            id="search-%s"
                            value="%s"/>''' % (criterion.Field(),
                                criterion.Field(), value)
                elif criterion.meta_type in ['ATSelectionCriterion',
                                            'ATListCriterion']:
                    options = u''
                    if criterion.Value():
                        if len(criterion.Value()) ==1:
                            continue
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
                            criterion_field['input'] = u'''
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
                            criterion_field['input'] = u'''
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
                        criterion_field['input'] = u'''
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

                    criterion_field['input'] = self._daterange_criterion(
                        criterion.Field(), start_date, startval,
                        end_date, endval)

                    #criterion_field['input'] = daterange_criterion(criterion)
                else:
                    criterion_field['input'] = None
                criteria.append(criterion_field)
        return criteria


class FormViewletNG(FormViewlet):
    ''' displays the query form for new style collections'''

    def get_criteria(self):
        ''' combine request with topic criteria '''
        criteria = []
        query = queryparser.parseFormquery(self.context, self.context.getRawQuery())
        registry = getUtility(IRegistry)
        qsrr = QuerystringRegistryReader(registry)
        for raw_query in self.context.getRawQuery():
            criterion = qsrr()['indexes'][raw_query['i']]
            input_html = ''
            selected = self.request.get(raw_query['i'],None)
            id = raw_query['i'] + '_' + raw_query['o'].replace('.','_')
            if raw_query['o'] == 'plone.app.querystring.operation.selection.is':
                if len(raw_query['v'])==1:
                    continue
                if selected:
                    options = u'<option value="">All</option>'
                else:
                    options = u'<option selected="selected" value="">All</option>'
                for value in raw_query['v']:
                    is_selected = self._sel(value,selected)
                    optstr = u'<option value="%(value)s" %(selected)s >%(name)s</option>'
                    options += optstr % {
                                        'value': value,
                                        'selected': is_selected,
                                        'name': value}
                    input_html = u'''
                        <select id="%s" name="%s">
                        %s
                        </select>''' % ( id,
                            raw_query['i'], options)
            elif raw_query['o']=='plone.app.querystring.operation.string.contains':
                value = self.request.get(raw_query['i'],'')
                input_html = u'''<input type="text"
                            size="25"
                            id="search-%s"
                            name="%s"
                            value="%s"/>''' % (id,
                                raw_query['i'], value)
            elif raw_query['o'] in DATERANGE_OPERATORS:
                start_date, end_date = get_start_end_ng(self.context, query,
                                                raw_query,
                                                self.portal_catalog)
                startval = self.request.get('start-' + raw_query['i'],
                            start_date.strftime('%Y/%m/%d'))
                endval = self.request.get('end-' + raw_query['i'],
                            end_date.strftime('%Y/%m/%d'))
                input_html = self._daterange_criterion(
                        raw_query['i'], start_date, startval,
                        end_date, endval)

            elif raw_query['o']=='plone.app.querystring.operation.date.largerThanRelativeDate':
                #within last n days
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.beforeToday':
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.lessThanRelativeDate':
                #within next n days
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.largerThan':
                #after date
                import ipdb; ipdb.set_trace()
            elif raw_query['o']=='plone.app.querystring.operation.date.today':
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.afterToday':
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.lessThan':
                # before date
                pass
            elif raw_query['o']=='plone.app.querystring.operation.date.between':
                # between date and date
                pass
            else:
                continue

            criterion_field = {
                'id': raw_query['i'] + '_' + raw_query['o'].replace('.','_'),
                'description': criterion['description'],
                'label': criterion['title'],
                'field': raw_query['i'],
                'input': input_html,
                }
            criteria.append(criterion_field)
        return criteria

class FlexigridViewlet(BaseViewlet):
    ''' displays the flexigrid results'''

class ResultTableViewlet(BaseViewlet):
    '''plain html results table '''


    def get_table_fields(self):
        return get_topic_table_fields(self.context, self.portal_catalog)

    def render_table(self, search_results):
        return get_renderd_table(self, search_results)

    def search_results(self):
        results = get_search_results(self)
        results['fields'] = self.get_table_fields()
        results['id'] = "topichtmlresults"
        results['display_legend'] = (results['num_results'] > 0)
        return results

class ResultTableViewletNG(ResultTableViewlet):

    def search_results(self):
        results = get_search_results_ng(self)
        results['fields'] = self.get_table_fields()
        results['id'] = "topichtmlresults"
        results['display_legend'] = (results['num_results'] > 0)
        return results



class JsViewlet(BaseViewlet):
    ''' inserts the js to render the above viewlets '''


    render = ViewPageTemplateFile("templates/jstemplate.pt")


    js_template = """
 $(document).ready(function() {
   $('#flexitopicsearchform').find('select').each(function(i) {
     $(this).change(function( objEvent ){
         $('#flexitopicresults').flexOptions({newp: 1}).flexReload();
        }) ;
   });
   $('#flexitopicsearchform').find('input:radio').each(function(i) {
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
            showTableToggleBtn: false,
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

    add_form_data_js ='//%s'


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
        def is_date(sortname):
            if sortname in IDX_METADATA and sortname !='Title':
                return True
            elif sortname in self.portal_catalog.Indexes.keys():
                if self.portal_catalog.Indexes[sortname].meta_type in ['DateIndex']:
                    return True
            return False
        fields = get_topic_table_fields(self.context, self.portal_catalog)
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IFlexiTopicSettings)
        width=settings.flexitopic_width
        height=settings.flexitopic_height
        i_date = 0
        for field in fields:
            if is_date(field['name']):
                i_date += 1
        date_fields_width = DATE_FIELD_WIDTH * i_date
        if len(fields) > i_date:
            field_width=int(
                (width - date_fields_width - 18 -
                    (len(fields) * FG_PADDING_WIDTH))/
                (len(fields)-i_date))
        else:
            field_width = DATE_FIELD_WIDTH
        t = "{display: '%s', name : '%s', width : %i, sortable : %s, align: 'left', hide: false}"
        tl = []
        for field in fields:
            this_field_width = 0
            if is_date(field['name']):
                this_field_width = DATE_FIELD_WIDTH
            else:
                this_field_width = field_width
            if is_sortable(field['name']):
                sortable='true'
            else:
                sortable='false'
            tl.append( t % (self.context.translate(_(field['label'])),
                        field['name'], this_field_width, sortable))
        sort = ''
        if hasattr(self.context, 'listCriteria'):
            #old style collection
            for criterion in self.context.listCriteria():
                if criterion.meta_type =='ATSortCriterion':
                    sortname = criterion.getCriteriaItems()[0][1]
                    sortorder = 'asc'
                    if len(criterion.getCriteriaItems())==2:
                        if criterion.getCriteriaItems()[1][1] =='reverse':
                            sortorder = 'desc'
                    sort = "sortname: '%s', sortorder: '%s'," % (
                                sortname, sortorder)
        elif hasattr(self.context, 'getSort_on'):
            #new style collection
            sortname = self.context.getSort_on()
            sortorder = 'asc'
            if self.context.getSort_reversed():
                sortorder = 'desc'
            else:
                sortorder = 'asc'
            sort = "sortname: '%s', sortorder: '%s'," % (
                                sortname, sortorder)
        table_name = self.context.Title()
        url = self.context.absolute_url() + '/@@flexijson_view'
        try:
            items_ppage = self.context.getItemCount()
        except AttributeError:
            items_ppage = settings.items_pp
        add_form_data_js = self.add_form_data_js % self.context.absolute_url()
        if items_ppage==0:
            items_ppage = settings.items_pp
        js = self.js_template % {
                'url': url,
                'col_model': ', '.join(tl),
                'sort': sort,
                'title': table_name,
                'items_ppage': items_ppage,
                'add_js': add_form_data_js,
                'width': width,
                'height': height,
            }
        return js

