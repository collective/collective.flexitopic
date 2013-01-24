from zope.interface import Interface
from zope.viewlet.interfaces import IViewletManager


class IFlexiTopicView(Interface):
    """
    FlexiTopic view interface
    """

class IFlexiJsonView(Interface):
    """
    FlexiJson view interface
    """

# viewletmanger interfaces for FlexiTopicView

class IFlexiTopicTop(IViewletManager):
    ''' The top of a flexitopic page '''

class IFlexiTopicForm(IViewletManager):
    ''' Render the seach form '''

class IFlexiTopicFormExt(IViewletManager):
    ''' insert into the seach form '''


class IFlexiTopicBottom(IViewletManager):
    ''' The botom of a flexitopic page
       (the results table)
    '''
class IFlexiTopicJs(IViewletManager):
    '''Slot to insert the JS into a flexitopic page '''

