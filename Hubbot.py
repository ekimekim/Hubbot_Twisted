import platform, os, datetime, codecs, re, sqlite3
from twisted.words.protocols import irc
from twisted.internet import protocol, reactor
from IRCResponse import ResponseType, IRCResponse
from IRCMessage import IRCMessage, IRCUser, IRCChannel
import GlobalVars
from ModuleHandler import ModuleHandler


class Hubbot(irc.IRCClient):
    fingerReply = GlobalVars.finger

    versionNum = GlobalVars.version
    versionEnv = platform.platform()

    sourceURL = GlobalVars.source

    startTime = datetime.datetime.min

    def __init__(self, server, channels):
        self.nickname = "Hubbot"
        self.realname = self.nickname
        self.username = self.nickname
        self.versionName = self.nickname
        self.CommandChar = "+"
        self.admins = self.loadAdmins()

        self.server = server
        self.channels = channels
        channels[self.nickname] = IRCChannel(self.nickname)
        channels["Auth"] = IRCChannel("Auth")

        self.Quitting = False
        self.startTime = datetime.datetime.now()

        self.prefixesCharToMode = {"+":"v", "@":"o"}
        self.ignores = self.loadIgnores()
        self.moduleHandler = ModuleHandler(self)
        self.moduleHandler.AutoLoadModules()

    def signedOn(self):
        for channel in self.channels.keys():
            if channel is not self.nickname and channel is not "Auth":
                self.join(channel)

    def isupport(self, options):
        for item in options:
            if "=" in item:
                option = item.split("=")
                if option[0] == "PREFIX":
                    prefixes = option[1]
                    statusModes = prefixes[:prefixes.find(")")]
                    statusChars = prefixes[prefixes.find(")"):]
                    for i in range(1, len(statusModes)):
                        self.prefixesCharToMode[statusChars[i]] = statusModes[i]


    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = self.channels[params[2]]

        if channel.NamesListComplete:
            channel.NamesListComplete = False
            channel.Users.clear()
            channel.Ranks.clear()

        channelUsers = params[3].split(" ")
        for channelUser in channelUsers:
            rank = ""
            if channelUser != "" and channelUser[0] in self.prefixesCharToMode:
                rank = self.prefixesCharToMode[channelUser[0]]
                channelUser = channelUser[1:]

            if channelUser not in channel.Users:
                user = IRCUser("{}!{}@{}".format(channelUser, "none", "none"))
            else:
                user = channel.Users[channelUser]

            channel.Users[user.Name] = user
            channel.Ranks[user.Name] = rank

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = self.channels[params[1]]
        channel.NamesListComplete = True

    def irc_NICK(self, prefix, params):
        userArray = prefix.split("!")
        oldnick = userArray[0]
        newnick = params[0]

        for key in self.channels:
            channel = self.channels[key]
            for userKey in channel.Users:
                user = channel.Users[userKey]
                if userKey == oldnick:
                    channel.Users[newnick] = IRCUser("{}!{}@{}".format(newnick, user.User, user.Hostmask))
                    del channel.Users[oldnick]
                    if oldnick in channel.Ranks:
                        channel.Ranks[newnick] = channel.Ranks[oldnick]
                        del channel.Ranks[oldnick]
                    message = IRCMessage('NICK', prefix, channel, newnick, self)
                    self.moduleHandler.handleMessage(message)

    def irc_JOIN(self, prefix, params):
        channel = self.channels[params[0]]
        message = IRCMessage('JOIN', prefix, channel, '', self)

        if message.User.Name != self.nickname:
            channel.Users[message.User.Name] = message.User
        self.moduleHandler.handleMessage(message)

    def irc_PART(self, prefix, params):
        partMessage = u''
        if len(params) > 1:
            partMessage = u', message: ' + u' '.join(params[1:])
        if params[0] in self.channels.keys():
            channel = self.channels[params[0]]
        else:
            channel = IRCChannel(params[0])
        message = IRCMessage('PART', prefix, channel, partMessage, self)

        if message.User.Name != self.nickname:
            del channel.Users[message.User.Name]
            if message.User.Name in channel.Ranks:
                del channel.Ranks[message.User.Name]
        self.moduleHandler.handleMessage(message)

    def irc_KICK(self, prefix, params):
        kickMessage = u''
        if len(params) > 2:
            kickMessage = u', message: ' + u' '.join(params[2:])

        channel = self.channels[params[0]]
        message = IRCMessage('KICK', prefix, channel, kickMessage, self)
        kickee = params[1]
        if kickee == self.nickname:
            del self.channels[message.ReplyTo]
        else:
            del channel.Users[kickee]
            if kickee in channel.Ranks:
                del channel.Ranks[kickee]
        self.moduleHandler.handleMessage(message)

    def irc_QUIT(self, prefix, params):
        quitMessage = u''
        if len(params) > 0:
            quitMessage = u', message: ' + u' '.join(params[0:])
        for key in self.channels:
            channel = self.channels[key]
            message = IRCMessage('QUIT', prefix, channel, quitMessage, self)
            if message.User.Name in channel.Users:
                del channel.Users[message.User.Name]
                if message.User.Name in channel.Ranks:
                    del channel.Ranks[message.User.Name]
            self.moduleHandler.handleMessage(message)

    def privmsg(self, user, channel, msg):
        message = IRCMessage('PRIVMSG', user, self.channels[channel], msg, self)
        for (name, module) in self.moduleHandler.modules.items():
            if message.Command in module.triggers:
                self.log(u'<{0}> {1}'.format(message.User.Name, message.MessageString), message.ReplyTo)
                break
        self.moduleHandler.handleMessage(message)

    def action(self, user, channel, msg):
        message = IRCMessage('ACTION', user, self.channels[channel], msg, self)
        pattern = "hu+g|cuddle|snu+ggle|snu+g|squeeze|glomp"
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            self.log(u'*{0} {1}*'.format(message.User.Name, message.MessageString), message.ReplyTo)
        self.moduleHandler.handleMessage(message)

    def noticed(self, user, channel, msg):
        message = IRCMessage('NOTICE', user, self.channels[channel], msg.upper(), self)
        self.log(u'[{0}] {1}'.format(message.User.Name, message.MessageString), message.ReplyTo)
        self.moduleHandler.handleMessage(message)

    def nickChanged(self, nick):
        self.nickname = nick

    def log(self, text, target):
        now = datetime.datetime.now()
        time = now.strftime("[%H:%M]")
        data = u'{0} {1}'.format(time, text)
        print target, data

        fileName = "{0}{1}.txt".format(target, now.strftime("-%Y%m%d"))
        fileDirs = os.path.join(GlobalVars.logPath, self.server)
        if not os.path.exists(fileDirs):
            os.makedirs(fileDirs)
        filePath = os.path.join(fileDirs, fileName)

        with codecs.open(filePath, 'a+', 'utf-8') as f:
            f.write(data + '\n')

    def notifyUser(self, flag, message):
        if flag:
            self.moduleHandler.sendResponse(IRCResponse(ResponseType.Say, "{}: Your {} second timer is up!".format(message.User.Name, message.ParameterList[0]), message.ReplyTo))
        else:
            self.moduleHandler.sendResponse(IRCResponse(ResponseType.Say, "{}: Your {} timer is up!".format(message.User.Name, " ".join(message.ParameterList)), message.ReplyTo))

    def loadIgnores(self):
        ignores = []
        with sqlite3.connect("data/data.db") as conn:
            c = conn.cursor()
            for row in c.execute("SELECT nick FROM ignores"):
                ignores.append(row[0])
        return ignores

    def loadAdmins(self):
        admins = []
        with sqlite3.connect("data/data.db") as conn:
            c = conn.cursor()
            for row in c.execute("SELECT nick FROM admins"):
                admins.append(row[0])
        return admins

class HubbotFactory(protocol.ReconnectingClientFactory):
    def __init__(self, server, port, channels):
        self.port = port
        self.protocol = Hubbot(server, channels)
        reactor.connectTCP(server, port, self)

    def startedConnecting(self, connector):
        print "-#- Started to connect to '{}'.".format(self.protocol.server)

    def buildProtocol(self, addr):
        print "-#- Connected to '{}'.".format(self.protocol.server)
        print "-#- Resetting reconnection delay."
        self.resetDelay()
        return self.protocol

    def clientConnectionLost(self, connector, reason):
        if not self.protocol.Quitting:
            print "-!- Connection lost. Reason:", reason
            protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print "-!- Connection failed. Reason:", reason
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
