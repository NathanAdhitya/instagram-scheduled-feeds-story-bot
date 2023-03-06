from instagrapi import Client
import json
import os

from dotenv import load_dotenv
load_dotenv()

cl = Client()
cl.login(os.environ.get("ACCOUNT_USERNAME"),
         os.environ.get("ACCOUNT_PASSWORD"))
print("Session ID: ", cl.sessionid)


# Data to be written
dictionary = {
    "sessionid": cl.sessionid,
}

with open("session.json", "w") as outfile:
    json.dump(dictionary, outfile)
