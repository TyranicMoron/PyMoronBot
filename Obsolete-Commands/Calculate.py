from IRCMessage import IRCMessage
from IRCResponse import IRCResponse, ResponseType
from CommandInterface import CommandInterface
import WebUtils

import re
import json
import urllib
import HTMLParser

class Command(CommandInterface):
    triggers = ['calc', 'calculate']
    help = "calc <expr> - Uses Google's calculation API to give you the result of <expr>"
    
    htmlParser = HTMLParser.HTMLParser()
    
    def execute(self, message):
        if len(message.ParameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give an expression to calculate! %s" % self.help, message.ReplyTo)
        
        query = urllib.quote(message.Parameters.encode('utf8'))
        j = WebUtils.SendToServer('http://www.google.com/ig/calculator?hl=en&q=' + query)
        j = re.sub(r"{\s*'?(\w)", r'{"\1', j)
        j = re.sub(r",\s*'?(\w)", r',"\1', j)
        j = re.sub(r"(\w)'?\s*:", r'\1":', j)
        j = re.sub(r":\s*'(\w)'\s*([,}])", r':"\1"\2', j)
        j = self.htmlParser.unescape(j)
        j = j.replace('\xa0', ',')
        j = j.replace('\\x3c', '<')
        j = j.replace('\\x3e', '>')
        j = j.replace('<sup>', '^(')
        j = j.replace('</sup>', ')')
        print j
        result = json.loads(j)
        
        if len(result['rhs']) > 0:
            return IRCResponse(ResponseType.Say, "{1}'s Result: {0}".format(result['rhs'], message.User.Name), message.ReplyTo)
        if len(result['error']) > 0:
            return IRCResponse(ResponseType.Say, 'Calculation Error or Unsupported Operations', message.ReplyTo)
