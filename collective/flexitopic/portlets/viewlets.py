import logging

logger = logging.getLogger(__name__)

from collective.flexitopic.browser import viewlets

class FormViewlet(viewlets.FormViewlet):
    """ Subclass Formviewlet to view with portlet"""

    def __init__(self, context, request, view, manager=None):
        super(FormViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()

    def get_view_name(self):
        return self.view.collection().absolute_url()

class FlexigridViewlet(viewlets.FlexigridViewlet):
    """ Display the flexigrid"""

class ResultTableViewlet(viewlets.ResultTableViewlet):
    """ no script variant of the resulttable"""

    def __init__(self, context, request, view, manager=None):
        super(ResultTableViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()

class JsViewlet(viewlets.JsViewlet):
    """ get JS to display flexigrid"""

    def __init__(self, context, request, view, manager=None):
        super(JsViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()
