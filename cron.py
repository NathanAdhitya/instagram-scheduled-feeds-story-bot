from os.path import isfile, join
from os import listdir, rename
from instagrapi import Client
from jsonschema import validate
from datetime import datetime, timedelta
import dateutil.parser
import json
import traceback
from utils.gotify_util import send_notification

from instagrapi.types import Usertag, Location
from instagrapi.types import StoryMention, StoryMedia
from instagrapi.types import StoryMention, StoryMedia, StoryLink, StoryHashtag
from time import sleep

from instagrapi.mixins.challenge import ChallengeChoice


PATH_PENDING = "data/pending"
PATH_FAILED = "data/failed"
PATH_DONE = "data/done"
PATH_PICS = "data/pics"

schema = None
with open("schema.json") as f:
    schema = json.load(f)
    f.close()

# Get sessionid & prep client
assert schema != None


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.SMS:
        return input("Challenge (SMS):")
    elif choice == ChallengeChoice.EMAIL:
        return input("Challenge (EMAIL):")
    return False


cl = Client()
cl.challenge_code_handler = challenge_code_handler
cl.load_settings("session.json")

# Get pending posts

pendingfiles = [f for f in listdir(PATH_PENDING) if isfile(
    join(PATH_PENDING, f)) and f.endswith(".json")]

for f in pendingfiles:
    try:
        fd = open(join(PATH_PENDING, f), encoding="utf-8")
        data = None
        try:
            data = json.load(fd)
        except Exception as e:
            fd.close()
            raise e

        fd.close()
        validate(instance=data, schema=schema)

        # Post if past or is the correct datetime
        expected_post_date = dateutil.parser.isoparse(
            data.get("publish_datetime")
        )

        # Make sure destination pics do exist.
        if data.get("image_src") is not None:
            if not isfile(join(PATH_PICS, data.get("image_src"))):
                raise Exception(
                    "Invalid image_src path. (File not found/is not file)")
        elif data.get("album") is not None:
            if False in [isfile(join(PATH_PICS, pic)) for pic in data.get("album")]:
                raise Exception(
                    "Invalid image_src path. (File not found/is not file)")
        else:
            raise Exception("No photo/album found in JSON.")

        if data.get("type") != "FEED" and data.get("type") != "STORY":
            raise Exception("'type' should be 'FEED' or 'STORY'")

        if datetime.now(expected_post_date.tzinfo) < expected_post_date:
            print(
                f"{f} is scheduled to be posted after {expected_post_date}, skipping.")
            continue

        if datetime.now(expected_post_date.tzinfo) - timedelta(days=1) > expected_post_date:
            raise Exception(
                f"{f} is at least one day late, expected {expected_post_date}, marking failed.")
            continue

        print(f"{f} is due at {expected_post_date}, posting now...")

        # Post the actual thing.
        if data.get("type") == "FEED":
            # Resolve mentions
            raw_mentions = data.get("tags")
            user_mentions = [cl.user_info_by_username(
                u) for u in raw_mentions]
            feed_mentions = [Usertag(user=u, x=0.5, y=0.5)
                             for u in user_mentions]

            if data.get("image_src") is not None:
                cl.photo_upload(
                    join(PATH_PICS, data.get("image_src")), data.get("caption"), usertags=feed_mentions
                )
            elif data.get("album") is not None:
                cl.album_upload(
                    [join(PATH_PICS, pic) for pic in data.get("album")], data.get("caption"), usertags=feed_mentions
                )

            # sleep(8)
            # # edit caption since it did not work first try most of the time
            # cl.media_edit(new_feed.pk, data.get("caption"))
        elif data.get("type") == "STORY":
            # Resolve mentions
            raw_mentions = data.get("tags")
            user_mentions = [cl.user_info_by_username(
                u) for u in raw_mentions]
            story_mentions = []

            mention_y = 0
            for u in user_mentions:
                story_mentions.insert(0, StoryMention(
                    user=u, x=0.5, y=mention_y, width=0.8, height=0.1))
                mention_y += 0.1

            links = []
            if data.get("link"):
                links.insert(0, StoryLink(webUri=data.get("link")))

            caption = " ".join(["@"+mention for mention in raw_mentions])

            cl.photo_upload_to_story(join(PATH_PICS, data.get(
                "image_src")), caption, mentions=story_mentions, links=links)

        rename(join(PATH_PENDING, f), join(PATH_DONE, f))
        print(f"Finished processing {f}")
        send_notification("Yay!", f"Posted {f} successfully")
    except Exception as e:
        print(f"Error reading {f}, {e}")
        send_notification(str(e), f"Failed to post {f}")
        traceback.print_exc()
        rename(join(PATH_PENDING, f), join(PATH_FAILED, f))

print("Script finished.")
