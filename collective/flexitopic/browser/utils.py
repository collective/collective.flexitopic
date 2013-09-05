#utils
import logging
from time import time
from DateTime import DateTime
from zope.component import getUtility
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.memoize import ram
try:
    from plone.app.querystring import queryparser
except ImportError:
    pass
from plone.registry.interfaces import IRegistry

from collective.flexitopic.interfaces import IFlexiTopicSettings
from collective.flexitopic import flexitopicMessageFactory as _
try:
    from plone.app.querystring import queryparser
except ImportError:
    pass

logger = logging.getLogger('collective.flexitopic')

logger.setLevel(logging.DEBUG)

# just to cheat i18ndude
title = _('Title')
phone = _('Phone')

RAM_CACHE_SECONDS = 60

DATERANGE_OPERATORS = [
    'plone.app.querystring.operation.date.largerThanRelativeDate', #within next n days
    'plone.app.querystring.operation.date.beforeToday',
    'plone.app.querystring.operation.date.lessThanRelativeDate', #within last n days
    'plone.app.querystring.operation.date.largerThan', #after date
    #'plone.app.querystring.operation.date.today',
    'plone.app.querystring.operation.date.afterToday',
    'plone.app.querystring.operation.date.lessThan', # before date
    'plone.app.querystring.operation.date.between', # between date and date
    ]

IDX_METADATA = {
        'Title': 'sortable_title',
        'ExpirationDate': 'expires',
        'ModificationDate': 'modified',
        'EffectiveDate': 'effective',
        'CreationDate': 'created'}

def _datelimit_cachekey(fun, context, criterion, portal_catalog):
    query = context.buildQuery()
    query.pop(criterion.Field(),None)
    ckey = list(context.getPhysicalPath())
    for dcriterion in context.listCriteria():
        if dcriterion.meta_type in ['ATFriendlyDateCriteria']:
            query.pop(criterion.Field(),None)
    ckey.append(query)
    ckey.append(criterion.Field())
    ckey.append(time() // RAM_CACHE_SECONDS)
    return ckey

@ram.cache(_datelimit_cachekey)
def get_date_limit(context, criterion, portal_catalog):
    '''
    get the earliest/latest date that should be included in
    a daterange covering all dates defined by the criteria
    '''
    query = context.buildQuery()
    query['sort_on'] = criterion.Field()
    query['sort_limit'] = 1
    if criterion.getOperation() == 'less':
        query['sort_order'] = 'ascending'
        adjust = -1
    else:
        query['sort_order'] = 'descending'
        adjust = 1
    query.pop(criterion.Field())
    results = portal_catalog(**query)
    if len(results) > 0:
        date_limit = results[0][criterion.Field()] + adjust
    else:
        date_limit = DateTime()
    return date_limit

def get_start_end(flexitopic, criterion, catalog):
    #for old style collections
    if criterion.meta_type in ['ATDateRangeCriterion']:
        start_date = criterion.getStart()
        end_date = criterion.getEnd()
    elif criterion.meta_type in ['ATFriendlyDateCriteria']:
        date_base = criterion.getCriteriaItems()[0][1]['query']
        if date_base==None:
            date_base = DateTime()
        date_limit = get_date_limit(flexitopic.context, criterion,
                                    catalog)
        start_date = min(date_base, date_limit)
        end_date =  max(date_base, date_limit)
    return start_date, end_date


def get_first_date(criterion, query, catalog, sort_order):
    query['sort_on'] = criterion
    query['sort_limit'] = 1
    query['sort_order'] = sort_order
    results = catalog(**query)
    if len(results) > 0:
        date_limit = results[0][criterion] #+ adjust
    else:
        date_limit = DateTime()
    return date_limit

def get_max_date(criterion, query, catalog):
    return get_first_date(criterion, query, catalog, 'descending')


def get_min_date(criterion, query, catalog):
    return get_first_date(criterion, query, catalog, 'ascending')



def get_start_end_ng(context, query, raw, catalog):
    if raw['o']=='plone.app.querystring.operation.date.largerThanRelativeDate':
        #within last n days
        return query[raw['i']]['query'][0], query[raw['i']]['query'][1]
    elif raw['o']=='plone.app.querystring.operation.date.beforeToday':
        return get_min_date(raw['i'], query, catalog), DateTime()
    elif raw['o']=='plone.app.querystring.operation.date.lessThanRelativeDate':
        #within next n days
        return query[raw['i']]['query'][0], query[raw['i']]['query'][1]
    elif raw['o']=='plone.app.querystring.operation.date.largerThan':
        #after date
        return DateTime(raw['v']), get_max_date(raw['i'], query, catalog)
    elif raw['o']=='plone.app.querystring.operation.date.afterToday':
        return DateTime(), get_max_date(raw['i'], query, catalog)
    elif raw['o']=='plone.app.querystring.operation.date.lessThan':
        # before date
        return get_min_date(raw['i'], query, catalog), DateTime(raw['v'])
    elif raw['o']=='plone.app.querystring.operation.date.between':
        # between date and date
        return DateTime(raw['v'][0]), DateTime(raw['v'][1])
    else:
        logger.error('operation %s not supported' % raw['o'])




def get_renderd_table(context, search_results):
    """ Render results table

    @return: Resulting HTML code as Python string
    """
    table_template = ViewPageTemplateFile("templates/table.pt")
    return table_template(context, search_results=search_results)

def get_topic_table_fields(context, catalog):
    fields = context.getCustomViewFields()
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IFlexiTopicSettings)
    field_list =[]
    vocab = context.listMetaDataFields(False)
    col_width = int(settings.flexitopic_width/len(fields))
    for field in fields:
        if field in IDX_METADATA.keys():
            idx = catalog.Indexes[IDX_METADATA[field]].meta_type
        elif field in catalog.Indexes.keys():
            idx = catalog.Indexes[field].meta_type
        else:
            idx = None
        name = vocab.getValue(field, field)
        field_list.append({'name': field, 'label': name, 'idx_type': idx,
                            'col_width': col_width})
    return field_list


def _search_result_cachekey(fun, flexitopic):
    ckey = [flexitopic.request.form]
    ckey.append(flexitopic.context.getPhysicalPath())
    ckey.append(time() // RAM_CACHE_SECONDS)
    return ckey


@ram.cache(_search_result_cachekey)
def get_search_results(flexitopic):
    form = flexitopic.request.form

    batch_size = form.get('b_size', 20)
    batch_start = form.get('b_start', 0)
    catalog = flexitopic.portal_catalog
    query = flexitopic.context.buildQuery()
    for criterion in flexitopic.context.listCriteria():
        if criterion.meta_type in ['ATDateRangeCriterion',
                                    'ATFriendlyDateCriteria']:
            start_date, end_date = get_start_end(flexitopic, criterion, catalog)
            value = (form.get('start-' + criterion.Field(),
                            start_date.strftime('%Y/%m/%d')),
                    form.get('end-' + criterion.Field(),
                            end_date.strftime('%Y/%m/%d')))
        else:
            value = form.get(criterion.Field(),None)
        if value:
            query[criterion.Field()] = {}
            if hasattr(criterion, 'getOperator'):
                operator = criterion.getOperator()
                query[criterion.Field()]['operator'] = operator
                assert(criterion.meta_type in
                        ['ATSelectionCriterion',
                        'ATListCriterion'])
            else:
                operator = None
            if operator =='or':
                query[criterion.Field()] = { 'query':[value],
                    'operator':'or'}
            elif operator == 'and':
                q = list(criterion.Value()) + [value]
                query[criterion.Field()] = { 'query':[q],
                    'operator':'and'}
            else:
                if criterion.meta_type in ['ATDateRangeCriterion',
                            'ATFriendlyDateCriteria']:
                    start = DateTime(value[0])
                    end = DateTime(value[1])
                    query[criterion.Field()] = {'query':(start, end),
                                'range': 'min:max'}

                else:
                    assert(criterion.meta_type=='ATSimpleStringCriterion')
                    if criterion.Value():
                        query[criterion.Field()] =  { 'query':
                                    [criterion.Value(), value],
                                    'operator':'and'}
                    else:
                        query[criterion.Field()] = value
        else:
            continue

    sortorder = form.get('sortorder',None)

    if sortorder=='desc':
        sort_order = 'reverse'
    else:
        sort_order = None
    sort_on = None
    sortname = form.get('sortname',None)
    if sortname in IDX_METADATA.keys():
        sort_on = IDX_METADATA[sortname]
    elif sortname in catalog.Indexes.keys():
        if catalog.Indexes[sortname].meta_type in [
                'FieldIndex', 'DateIndex', 'KeywordIndex']:
            sort_on = sortname
    elif sortname == None:
        #get sort_on/order out of topic
        for criterion in flexitopic.context.listCriteria():
            if criterion.meta_type =='ATSortCriterion':
                sort_on = criterion.getCriteriaItems()[0][1]
                if len(criterion.getCriteriaItems())==2 and sortorder==None:
                    sort_order = criterion.getCriteriaItems()[1][1]
    if sort_on:
        query['sort_on'] = sort_on
        if sort_order:
            query['sort_order'] = sort_order

    logger.debug(query)
    results = catalog(**query)

    return {'results': results, 'size': batch_size,
        'start': batch_start, 'num_results': len(results)}

def get_search_results_ng(flexitopic):
    form = flexitopic.request.form

    batch_size = form.get('b_size', 20)
    batch_start = form.get('b_start', 0)
    catalog = flexitopic.portal_catalog
    query = queryparser.parseFormquery(flexitopic.context,
            flexitopic.context.getRawQuery())
    for raw_query in flexitopic.context.getRawQuery():
            value = form.get(raw_query['i'], False)
            if value:
                if (
                (raw_query['o'] == 'plone.app.querystring.operation.selection.is')
                and (value in raw_query['v'])):
                    query[raw_query['i']]['query'] = value
                elif raw_query['o'] == 'plone.app.querystring.operation.string.contains':
                    if raw_query['v']:
                        query[raw_query['i']]['query'] = value + ' AND ' + raw_query['v']
                    else:
                        query[raw_query['i']]['query'] = value
            elif raw_query['o'] in DATERANGE_OPERATORS:
                start = form.get('start-' + raw_query['i'], False)
                end = form.get('end-' + raw_query['i'], False)
                if start and end:
                    query[raw_query['i']] = {'query':(start, end),
                                'range': 'min:max'}


    sortorder = form.get('sortorder',None)

    if sortorder=='desc':
        sort_order = 'reverse'
    else:
        sort_order = None
    sort_on = None
    sortname = form.get('sortname',None)
    if sortname in IDX_METADATA.keys():
        sort_on = IDX_METADATA[sortname]
    elif sortname in catalog.Indexes.keys():
        if catalog.Indexes[sortname].meta_type in [
                'FieldIndex', 'DateIndex', 'KeywordIndex']:
            sort_on = sortname
    elif sortname == None:
        #get sort_on/order out of topic
        sort_on = flexitopic.context.getSort_on()
        if flexitopic.context.getSort_reversed():
            sort_order = 'reverse'
    if sort_on:
        query['sort_on'] = sort_on
        if sort_order:
            query['sort_order'] = sort_order
    logger.debug(query)
    results = catalog(**query)
    return {'results': results, 'size': batch_size,
        'start': batch_start, 'num_results': len(results)}
