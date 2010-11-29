  # -*- extra stuff goes here -*- 
from zope.i18nmessageid import MessageFactory

flexitopicMessageFactory = MessageFactory('collective.flexitopic')

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
