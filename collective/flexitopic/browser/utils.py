#utils

from Products.CMFCore.utils import getToolByName

IDX_METADATA = {
        'Title': 'sortable_title',
        'ExpirationDate': 'expires',
        'ModificationDate': 'modified',
        'EffectiveDate': 'effective',
        'CreationDate': 'created'}


def get_topic_table_fields(context, catalog):
    fields = context.getCustomViewFields()
    field_list =[]
    vocab = context.listMetaDataFields(False)
    for field in fields:
        if field in IDX_METADATA.keys():
            idx = catalog.Indexes[IDX_METADATA[field]].meta_type
        elif field in catalog.Indexes.keys():
            idx = catalog.Indexes[field].meta_type
        else:
            idx = None
        name = vocab.getValue(field, field)
        field_list.append({'name': field, 'label': name, 'idx_type': idx})
    return field_list


def get_search_results(flexitopic):
    form = flexitopic.request.form

    batch_size = form.get('b_size', 20)
    batch_start = form.get('b_start', 0)
    catalog = flexitopic.portal_catalog
    query = {}
    for criterion in flexitopic.context.listCriteria():
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
                assert(criterion.meta_type=='ATSimpleStringCriterion')
                if criterion.Value():
                    query[criterion.Field()] = criterion.Value() + \
                        ' AND ' + value
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
