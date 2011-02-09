# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" Metrology connector Pubsub client. """
from __future__ import with_statement
import sys, os

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application import service


from vigilo.common.gettext import translate
from vigilo.connector import client, options

_ = translate('vigilo.connector_metro')

class MetroConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """
    implements(service.IServiceMaker, IPlugin)
    tapname = "vigilo-metro"
    description = "Vigilo connector for performance data"
    options = options.Options

    def makeService(self, options):
        """ the service that wraps everything the connector needs. """
        from vigilo.common.conf import settings
        settings.load_module('vigilo.connector_metro')

        from vigilo.common.logging import get_logger
        LOGGER = get_logger('vigilo.connector_metro')

        from vigilo.connector_metro.nodetorrdtool import NodeToRRDtoolForwarder

        try:
            conf_ = settings['connector-metro']['config']
        except KeyError:
            LOGGER.error(_("Please set the path to the configuration "
                "database generated by VigiConf in the settings.ini."))
            sys.exit(1)

        xmpp_client = client.client_factory(settings)

        try:
            message_consumer = NodeToRRDtoolForwarder(conf_)
        except OSError, e:
            LOGGER.exception(e)
            raise
        message_consumer.setHandlerParent(xmpp_client)

        # Présence
        from vigilo.connector.presence import PresenceManager
        presence_manager = PresenceManager()
        presence_manager.setHandlerParent(xmpp_client)

        # Statistiques
        from vigilo.connector.status import StatusPublisher
        servicename = options.get("name", "vigilo-connector-metro")
        stats_publisher = StatusPublisher(message_consumer,
                            settings["connector"].get("hostname", None),
                            servicename=servicename)
        stats_publisher.setHandlerParent(xmpp_client)

        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service

metro_connector = MetroConnectorServiceMaker()