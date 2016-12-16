import requests
from json.decoder import JSONDecoder
import json
from bs4 import BeautifulSoup
from delorean import Delorean

from pprint import pprint
import time

#custom classes
from errors import ValidationError,UnknownParticipantError
from conversation import Conversation


class TumblrMessaging(object):
    _headers = None
    _urls = None
    _internal_form_key = None
    _bootloader = None
    _conversation_partners = dict()  # uuid: conversation_id


    def __init__(self, email, password, blog):
        self._email = email
        self._password = password
        self._blog = blog

        self._session = requests.session()
        self._init_headers()
        self._init_urls()

        self._login()
        self._get_conversation_ids()

    def _init_headers(self):
        self._headers = {
            'login': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0 Iceweasel/44.0.2',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.tumblr.com/login'
            },
            'ajax': {
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'X-tumblr-form-key': self._internal_form_key,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'User-Agent': 'Mozilla/5.0 (x11; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0 Iceweasel/44.0.2',
                'Referer': 'https://www.tumblr.com/dashboard',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }

    def _init_urls(self):
        self._urls = {
            'login': 'https://www.tumblr.com/login',
            'message': 'https://www.tumblr.com/svc/conversations/messages',
            'participant_suggestions': 'https://www.tumblr.com/svc/conversations/participant_suggestions',
            'conversation_poll': 'https://www.tumblr.com/svc/conversations',
            'poll': 'https://www.tumblr.com/services/poll',
            'conversations' : 'https://www.tumblr.com/svc/conversations?participant=leftistnaija.tumblr.com&_=1',
            'conversations1' : 'https://www.tumblr.com/svc/conversations?participant=leftistnaija.tumblr.com&_=1481691647264',
        }

    def _login(self):
        pre_login_soup = BeautifulSoup(self._session.get(self._urls['login']).text, 'lxml')
        login_form_key = pre_login_soup.find(id='tumblr_form_key')['content']

        r = self._session.post(self._urls['login'], data={
            'determine_email': self._email,
            'user[email]': self._email,
            'user[password]': self._password,
            'version': 'STANDARD',
            'form_key': login_form_key,
            'tumblelog[name]': '',
            'user[age]': '',
            'context': 'no_referer',
            'follow': '',
            'seen_suggestion': '0',
            'used_suggestion': '0',
            'used_auto_suggestion': '0',
            'about_tumblr_slide': ''
        }, headers=self._headers['login'])

        r.raise_for_status()

        if 'dashboard' not in r.url:
            raise ValidationError
        else:
            post_login_soup = BeautifulSoup(r.text, 'lxml')
            self._internal_form_key = post_login_soup.find(id='tumblr_form_key')['content']
            # reload headers
            self._init_headers()
            # parse bootloader the quick 'n dirty way
            raw_bootloader = str(post_login_soup.find(id='bootloader')['data-bootstrap'])
            raw_bootloader.replace('&quot;', '"')
            self._bootloader = JSONDecoder().decode(raw_bootloader)

    def send_message(self, recipient, message):
        d = Delorean(timezone='GMT')

        r = self._session.post(self._urls['message'], data={
            'content[text]': message,
            'post[type]': '',
            'post[summary]': '',
            'post[state]': '',
            'hasAnimation': 'true',
            'clientTs': d.format_datetime('%a %b %d %Y %H:%M:%S (%Z)'),
            'isPending': 'true',
            'type': 'TEXT',
            'message': message,
            'ts': '',
            'participant': self._blog,
            'collapseGroup': 'new',
            'tsHeader': 'Today at {0}'.format(d.format_datetime('%I:%M %p')),
            'isError': 'false',
            'isCollapsed': 'false',
            'canRetry': 'true',
            'postHasTextMessage': 'false',
            'context': '',
            'participants[]': [self._blog, recipient]
        }, headers=self._headers['ajax'])

        r.raise_for_status()
        returnedJson = r.json()
        with open("sendMessageReceipt.json","w") as f:
            f.write(json.dumps(returnedJson,indent=2))
        return returnedJson['response']['id']

    def get_people(self):
        r = self._session.get(self._urls['conversation_poll'], headers=self._headers['ajax'],
                                                            params={'participant':self._blog,
                                                                    '_':1 })
        print(int((time.time())*1000))
        r.raise_for_status()
        with open("conversationOutput2.json","w") as f:
            f.write(json.dumps(r.json(),indent=2))

    def get_messages(self, conversation_id):
        r = self._session.get(self._urls['message'], headers=self._headers['ajax'],
                              params={'conversation_id': conversation_id, 'participant': self._blog})

        r.raise_for_status()
        returnedJson = r.json()

        #with open("sampleMessages.json","w") as f:
        #    f.write(json.dumps(returnedJson,indent=2))
        return returnedJson['response']

    def get_conversation_suggestions(self, limit=8):
        r = self._session.get(self._urls['participant_suggestions'], headers=self._headers['ajax'],
                              params={'limit': limit})

        r.raise_for_status()
        rjson = r.json()
        #with open("conversationSuggestion.json","w") as f:
        #    f.write(json.dumps(rjson,indent=2))
        return rjson['response']

    def _get_conversation_ids(self):
        r = self._session.get(self._urls['conversation_poll'], headers=self._headers['ajax'],
                              params={'participant': self._blog})

        r.raise_for_status()
        rjson = r.json()

        #with open("conversationIDs.json","w") as f:
        #    f.write(json.dumps(rjson,indent=2))

        if '_links' in rjson['response']:
            self._urls['conversation_poll'] = 'https://www.tumblr.com{0}'.format(
                rjson['response']['_links']['next']['href']
            )
        if 'conversations' in rjson['response']:
            for conversation in rjson['response']['conversations']:
                # conversation_id = conversation['id']
                self._conversation_partners[conversation['participants'][1]['uuid']] = conversation

    def _poll(self):
        r = self._session.get('https://www.tumblr.com/services/poll', params={
            'token': self._bootloader['Context']['userinfo']['polling_token']}, headers=self._headers['ajax'])

        r.raise_for_status()
        with open("pollResults.json","w") as f:
            f.write(json.dumps(r.json(),indent=2))
        #return r.json()['response']

    def is_unread(self, participant):
        if participant not in self._conversation_partners:
            raise UnknownParticipantError
        else:
            return self._conversation_partners[participant]['last_modified_ts'] > \
                   self._conversation_partners[participant]['last_read_ts']


if __name__ == '__main__':
    userCredentials = None
    with open("userinfo.jl") as f:
        userCredentials = json.loads(f.read())
    tm = TumblrMessaging(userCredentials["username"], userCredentials["password"], userCredentials['blog'])

    cid = tm.send_message("thewritingduke.tumblr.com","Request for another conversation ID?")
    if (cid is not None):
        conversation = Conversation(tm.get_messages(cid))
        log = open("output2.txt", "w")
        print(conversation, file = log)

    #tm._get_conversation_ids()
    #print(tm._conversation_partners)
    #print(tm.is_unread('scullywannabe.tumblr.com'))

    #tm._get_conversation_ids()
    #cid = tm.send_message('scullywannabe.tumblr.com', 'hiiiiiiiiiiiii')
    #messages = tm.get_messages(cid)
    '''
    for message in messages:
        print('From: {0}'.format(message['participant']))
        print(message['message'])
        print('')
        '''
