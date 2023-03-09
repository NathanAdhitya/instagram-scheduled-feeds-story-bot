from instagrapi import Client
import json
import os

from dotenv import load_dotenv
load_dotenv()

cl = Client()

cl.login(os.environ.get("ACCOUNT_USERNAME"),
         os.environ.get("ACCOUNT_PASSWORD"))
print("Session ID: ", cl.sessionid)

cl.dump_settings("session.json")
