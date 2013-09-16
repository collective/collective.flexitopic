from zope.interface import Interface
from zope.viewlet.interfaces import IViewletManager

##### Viewlet managers ###########

class IFlexiTopicForm(IViewletManager):
    ''' Render the seach form '''

class IFlexiTopicTable(IViewletManager):
    ''' The botom of a flexitopic page
       (the results table)
    '''
class IFlexiTopicJs(IViewletManager):
    '''Slot to insert the JS into a flexitopic page '''
