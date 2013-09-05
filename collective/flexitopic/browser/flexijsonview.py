from types import StringTypes

from zope.interface import implements
from zope.component import getMultiAdapter
from interfaces import IFlexiJsonView
import logging

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

try:
    import simplejson as json
except ImportError:
    import json


from utils import get_search_results, get_topic_table_fields, get_search_results_ng

logger = logging.getLogger('collective.flexitopic')




class FlexiJsonView(BrowserView):
    """
    FlexiJson browser view
    """
    implements(IFlexiJsonView)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def site_properties(self):
        return getToolByName(self.context, 'portal_properties').site_properties

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def _get_search_results(self):
        return get_search_results(self)['results']

    def __call__(self):
        """
        Return JSON for flexigrid, the query form looks like:
        {'getAgencies': '', 'rp': '15', 'sortname': 'Title', 'Title': '',
        'getProject_status': '', 'getSubRegions': '', 'SearchableText': '',
        'getProject_type': '', 'sortorder': 'asc', 'query': '',
        'getBasin': '', 'qtype': 'getSubRegions', 'page': '1'}
        """
        util = getToolByName(self.context, 'translation_service')
        form = self.request.form
        limit = int(form.get('rp', '15'))
        start = (int(form.get('page', '1')) - 1) * limit
        end = start + limit + 1
        results = self._get_search_results()
        json_result= {"page":form.get('page', '1') ,
            "total":len(results),
            "rows":[]}
        fields = get_topic_table_fields(self.context, self.portal_catalog)
        layout = getMultiAdapter((self.context, self.request), name=u'plone_layout')
        use_view_action = self.site_properties.typesUseViewActionInListings
        for result in results[start:end]:
            cell = []
            icon = layout.getIcon(result)
            if icon.url:
                icon_snp = u'<img src="%s" alt="%s" title="%s" width="%i" height="%i" />'%(
                    icon.url, icon.description, icon.title, icon.width, icon.height)
            else:
                icon_snp = ''
            for field in fields:
                value = getattr(result, field['name'])
                if type(value)==tuple:
                    vt =[]
                    for v in value:
                        v = v.decode('utf-8', 'ignore').encode('ascii', 'xmlcharrefreplace')
                        vt.append(v)
                    value = vt
                elif type(value) in StringTypes:
                    value = value.decode('utf-8', 'ignore').encode('ascii', 'xmlcharrefreplace')
                if not value:
                    cell.append('')
                elif field['idx_type'] == 'DateIndex':
                    dateval = util.ulocalized_time( value,
                            context=self.context,
                            domain='plonelocales',
                            request=self.request)
                    cell.append(dateval)
                elif field['name']=='Title':
                    if result.portal_type in use_view_action:
                        a = u'<a href="%s/view">%s %s</a>'
                    else:
                        a = u'<a href="%s">%s %s</a>'
                    cell.append(a % (result.getURL(), icon_snp, value))
                elif type(value)==tuple:
                    cell.append(', '.join(getattr(result, field['name'])))
                else:
                    cell.append(value)

            json_result['rows'].append(
                {"id":result.getId,"cell":cell})

        self.request.RESPONSE.setHeader('Content-Type','application/json; charset=utf-8')
        return json.dumps(json_result)


class FlexiJsonViewNG(FlexiJsonView):
    """
    FlexiJson browser view
    """
    def _get_search_results(self):
        return get_search_results_ng(self)['results']

