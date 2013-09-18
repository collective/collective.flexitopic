import logging
from collective.flexitopic.browser import viewlets

logger = logging.getLogger(__name__)


class FormViewlet(viewlets.FormViewlet):
    """ Subclass Formviewlet to view with portlet"""

    def __init__(self, context, request, view, manager=None):
        super(FormViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()

    def get_view_name(self):
        return self.view.collection().absolute_url()


class FormViewletNG(viewlets.FormViewletNG):
    """ Subclass Formviewlet for (new style) Collections for portlet"""

    def __init__(self, context, request, view, manager=None):
        super(FormViewletNG, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()

    def get_view_name(self):
        return self.view.collection().absolute_url()



class ResultTableViewlet(viewlets.ResultTableViewlet):
    """ no script variant of the resulttable"""

    def __init__(self, context, request, view, manager=None):
        super(ResultTableViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()


class ResultTableViewletNG(viewlets.ResultTableViewletNG):
    """ Result table for (new style collections"""

    def __init__(self, context, request, view, manager=None):
        super(ResultTableViewletNG, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()


class JsViewlet(viewlets.JsViewlet):
    """ get JS to display flexigrid"""

    def __init__(self, context, request, view, manager=None):
        super(JsViewlet, self).__init__(context, request, view, manager)
        self.topic = self.view.collection()
        if self.view.data.flexitopic_width:
            self.flexitopic_width = self.view.data.flexitopic_width
        if self.view.data.flexitopic_height:
            self.flexitopic_height = self.view.data.flexitopic_height
        if self.view.data.limit:
            self.items_ppage = self.view.data.limit
