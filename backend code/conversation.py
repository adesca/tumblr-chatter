import requests
import shutil
from datetime import datetime
from collections import namedtuple

Message = namedtuple('Message', ['date','type','participant','content'])

class _ConversationState(object):
    '''
    Holds information across user sessions so we don't constantly ping tumblr
    for information.
    '''

    participantAvs = {}




class Conversation(object):
    participantList = []


    def __init__(self,sampleConversation):

        self.timeStamp = sampleConversation['last_modified_ts']
        self.cid = sampleConversation['id']
        self._setMessages(sampleConversation['messages'])

        participants = sampleConversation["participants"]
        for participant in participants:
            temp = {}
            temp['name'] = participant["name"]
            temp['title'] = participant["title"]
            temp['avatar'] = participant['avatar_url']
            result = self._getPicture(participant["avatar_url"],temp['name'])
            if result < 0:
                print("There was a problem getting the tumblr avatar for "+temp['name'])
            self.participantList.append(temp)

    def _setMessages(self,messageList):
        self.loadPrevLink = messageList['_links']['next']['href']
        messageData = messageList['data']
        self.messages = [self.__messageObjectFactory(message) for message in messageData]

    def __messageObjectFactory(self, message):
        date = datetime.fromtimestamp(int(message['ts'])/1000).strftime('%Y-%m-%d %H:%M:%S')
        messageType = message['type']
        messenger = message['participant']

        if messageType == 'TEXT':
            content = [message['message']]
        elif messageType == 'POSTREF':
            content = [photo['original_size']['url'] for photo in message['post']['photos']]
        else:
            content = "Unrecognized message type."
        return Message(date=date,type=messageType,participant=messenger,content=content)

    def _getPicture(self,avatarURL,name):
        r = requests.get(avatarURL, stream=True)
        if r.status_code == 200:
            with open(("conversations\\"+name+" av.png"), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            return 0
        else:
            return -1

    def __repr__(self):
        result = ""
        for participant in self.participantList:
            result += participant['name'] + "\t" + participant['title'] + "\t" + participant['avatar'] + "\n"
        result += "\n" + str(self.cid) + "\t" + str(self.timeStamp) + "\n\n"
        result += self.printMessages()
        return result

    def printMessages(self):
        messageString = ""
        for message in self.messages:
            messageString += message.date + "\t" + message.participant + "\n"
            for item in message.content:
                messageString += item + "\n"
        return messageString
