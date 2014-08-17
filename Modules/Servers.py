from IRCResponse import IRCResponse, ResponseType
from ModuleInterface import ModuleInterface


class Servers(ModuleInterface):

    def onLoad(self):
        self.help = "mumble, gmod, starbound, starbound2, jcmp, tetri, cockatrice, kf, tf2, minecraft -- Used to post server info for games! Usage: {}<server>".format(self.bot.CommandChar)
        self.serverDict = \
            {
                "servers":"",
                "mumble":'The mumble server is hosted at: mumble.dahou.se',
                "gmod":"List of mods needed for GMOD: http://bit.ly/dahousegmod\n The Garry's Mod server is hosted at: gmod.dahou.se",
                "starbound":"The Starbound server is hosted at: starbound.dahou.se",
                "starbound2":"Ricin's Starbound server is hosted at: sb.117.me",
                "jcmp":"Ricin's Just Cause 2 MP server is hosted at: jcmp.117.me",
                "tetri":"Ricin's Tetrinet server is hosted at: tn.ricin.us",
                "cockatrice":"The Cockatrice server is hosted at: cockatrice.dahou.se:4747",
                "kf":"The Killing Floor server is hosted at: kf.dahou.se",
                "tf2":"The Team Fortress 2 server is hosted at tf2.dahou.se",
                "minecraft":"The FTB Monster server is hosted at craft.dahou.se (PM MasterCheese for build permission)",
                "<server>":"Seriously?"
            }
        self.triggers.extend(self.serverDict.keys())

    def shouldTrigger(self, message):
        if message.Command in self.serverDict.keys() and message.Type in self.acceptedTypes:
            return True
        else:
            return False

    def onTrigger(self, message):
        if message.Command == "servers":
            return IRCResponse(ResponseType.Say, self.help, message.ReplyTo)
        else:
            return IRCResponse(ResponseType.Say, self.serverDict[message.Command], message.ReplyTo)