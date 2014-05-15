from IRCResponse import IRCResponse, ResponseType
from ModuleInterface import ModuleInterface
import GlobalVars


class Module(ModuleInterface):
    triggers = ["leave", "gtfo"]
    help = "leave/gtfo - makes the bot leave the current channel"

    def onTrigger(self, Hubbot, message):
        if message.User.Name not in GlobalVars.admins:
            return IRCResponse(ResponseType.Say, 'Only my admins can tell me to {}'.format(message.Command), message.ReplyTo)
        if len(message.ParameterList) > 0:
            Hubbot.channels.remove(message.ReplyTo)
            return IRCResponse(ResponseType.Raw, 'PART {} :{}'.format(message.ReplyTo, message.Parameters), '')
        else:
            Hubbot.channels.remove(message.ReplyTo)
            return IRCResponse(ResponseType.Raw, 'PART {} :toodles!'.format(message.ReplyTo), '')