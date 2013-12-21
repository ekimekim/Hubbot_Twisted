from twisted.application import internet, service
from hubbebot import *

import GlobalVars


application = service.Application("AllTheHubbeBots")

for (server, channels) in GlobalVars.connections.items():
    protocol = HubbeBot(server, channels)
    factory = HubbeBotFactory(protocol)
    internet.TCPClient(server, GlobalVars.port, factory).setServiceParent(application)