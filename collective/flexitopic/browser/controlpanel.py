from plone.app.registry.browser import controlpanel

from collective.flexitopic.interfaces import IFlexiTopicSettings, _


class FlexiTopicEditForm(controlpanel.RegistryEditForm):

    schema = IFlexiTopicSettings
    label = _(u"Flexitopic settings")
    description = _(u"""""")

    def updateFields(self):
        super(FlexiTopicEditForm, self).updateFields()


    def updateWidgets(self):
        super(FlexiTopicEditForm, self).updateWidgets()

class FlexiTopicControlPanel(controlpanel.ControlPanelFormWrapper):
    form = FlexiTopicEditForm
