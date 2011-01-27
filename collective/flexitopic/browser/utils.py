#utils
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from plone.memoize import ram
from time import time

from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from collective.flexitopic.interfaces import IFlexiTopicSettings

RAM_CACHE_SECONDS = 3600

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
        date_limit = None
    return date_limit

def get_start_end(flexitopic, criterion, catalog):
    if criterion.meta_type in ['ATDateRangeCriterion']:
        start_date = criterion.getStart()
        end_date = criterion.getEnd()
    elif criterion.meta_type in ['ATFriendlyDateCriteria']:
        date_base = criterion.getCriteriaItems()[0][1]['query']
        date_limit = get_date_limit(flexitopic.context, criterion,
                                    catalog)
        start_date = min(date_base, date_limit)
        end_date =  max(date_base, date_limit)
    return start_date, end_date



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
    query = {}
    for criterion in flexitopic.context.listCriteria():
        if criterion.meta_type in ['ATDateRangeCriterion',
                                    'ATFriendlyDateCriteria']:
            start_date, end_date = get_start_end(flexitopic, criterion, catalog)
            value = (flexitopic.request.get('start-' + criterion.Field(),
                            start_date.strftime('%Y/%m/%d')),
                    flexitopic.request.get('end-' + criterion.Field(),
                            end_date.strftime('%Y/%m/%d')))
        else:
            value = flexitopic.request.get(criterion.Field(),None)
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
                query[criterion.Field()] = [value]
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
            if criterion.getCriteriaItems():
                if criterion.meta_type in ['ATSortCriterion',]:
                    continue
                else:
                    assert(criterion.getCriteriaItems()[0][0]==criterion.Field())
                    query[criterion.Field()] = criterion.getCriteriaItems()[0][1]

    sortorder = form.get('sortorder',None)

    if sortorder=='desc':
        sort_order = 'reverse'
    else:
        sort_order = None
    sort_on = None
    sortname = form.get('sortname',None)
    if sortname in IDX_METADATA.keys():
        sort_on = IDX_METADATA[sortname]
    elif sortname in flexitopic.portal_catalog.Indexes.keys():
        if flexitopic.portal_catalog.Indexes[sortname].meta_type in [
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


    results = catalog(**query)

    return {'results': results, 'size': batch_size,
        'start': batch_start, 'num_results': len(results)}
