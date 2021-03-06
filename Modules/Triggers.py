from IRCResponse import IRCResponse, ResponseType
from ModuleInterface import ModuleInterface

class Triggers(ModuleInterface):
    triggers = ["triggers"]
    help = "triggers -- returns a list of all command triggers, must be over PM"

    def onTrigger(self, message):
        if message.User.Name != message.ReplyTo:
            return IRCResponse(ResponseType.Say, "{} must be used over PM!".format(message.Command), message.ReplyTo)
        else:
            response = ""
            for name, command in self.bot.moduleHandler.modules.iteritems():
                if len(command.triggers)>0:
                    for trigger in command.triggers:
                        if "<" not in trigger and trigger not in response:
                            response += "{}, ".format(trigger)
            return IRCResponse(ResponseType.Say, response, message.ReplyTo)