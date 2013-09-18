from zope.interface import Interface
from zope.viewlet.interfaces import IViewletManager

##### Viewlet managers ###########

class IFlexiTopicForm(IViewletManager):
    ''' Render the seach form for old style topics'''

class IFlexiTopicMap(IViewletManager):
    ''' placeholder for map for collective.geo.flexitopic'''

class IFlexiTopicTable(IViewletManager):
    ''' The botom of a flexitopic page
       (the results table for old style topics)
    '''

class IFlexiTopicFormNG(IViewletManager):
    ''' Render the seach form for new style cllections'''

class IFlexiTopicTableNG(IViewletManager):
    ''' The botom of a flexitopic page
       (the results table for new style collections)
    '''


class IFlexiTopicJs(IViewletManager):
    '''Slot to insert the JS into a flexitopic page '''
