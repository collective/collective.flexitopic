"""Define interfaces for your add-on.
"""
from plone.theme.interfaces import IDefaultPloneLayer

import zope.interface


class IFlexiTopicLayer(IDefaultPloneLayer):
    """Marker interface that defines a Zope 3 browser layer.
    """
