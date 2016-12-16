import json
from conversation import Conversation

tumblrJson = None
with open("conversationOutput.json") as f:
    tumblrJson = json.loads(f.read())

choice = input("Are we (0) parsing a conversation or (1) list of conversations? ")
print(choice)
if int(choice) is 0:
    with open("sampleMessages.json") as f:
        tempjson = json.loads(f.read())
    cObject = Conversation(tempjson["response"])
    log = open("output.txt", "w")
    print(cObject, file = log)
else:
    for conversation in tumblrJson["response"]["conversations"]:
        for participant in conversation["participants"]:
            if(participant["url"] != "http://leftistnaija.tumblr.com/"):
                print(participant["url"])
