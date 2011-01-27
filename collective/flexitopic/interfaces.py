"""Define interfaces for your add-on.
"""
from zope.interface import Interface
from zope import schema

from zope.i18nmessageid import MessageFactory
from plone.theme.interfaces import IDefaultPloneLayer

_ = MessageFactory('collective.akismet')

class IFlexiTopicLayer(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer.
    """

class IFlexiTopicSettings(Interface):
    """Global settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    flexitopic_width = schema.Int(title=_(u"Flexitopic width"),
                                  description=_(u"Width of the flexigrid table"),
                                  required=True,
                                  default=900)

    flexitopic_height = schema.Int(title=_(u"Flexitopic height"),
                                  description=_(u"Height of the flexigrid table"),
                                  required=True,
                                  default=200)
