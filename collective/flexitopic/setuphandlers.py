# -*- coding: utf-8 -*-
import logging
from Products.CMFCore.utils import getToolByName

# The profile id of your package:
PROFILE_ID = 'profile-collective.flexitopic:default'

def add_ng_collection(context, logger=None):
    if logger is None:
        # Called as upgrade step: define our own logger.
        logger = logging.getLogger('collective.flexitopic')
    logger.info("Add typeinfo for new style collections")
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')

def upgrade_registry(context, logger=None):  # pylint: disable=W0613
    """Re-import the portal configuration registry settings.
    """
    if logger is None:
        # Called as upgrade step: define our own logger.
        logger = logging.getLogger('collective.flexitopic')
    logger.info("Update registry")
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'plone.app.registry')
    return
