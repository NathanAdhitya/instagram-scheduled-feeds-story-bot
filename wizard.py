import os
import pathlib
import re
from os.path import join, isfile, isdir
from os import listdir
from dateparser import DateDataParser
import shutil
import json

ddp = DateDataParser(languages=['id', 'id'], settings={
                     'RETURN_AS_TIMEZONE_AWARE': True})

pending_dir = "./wizard_data/pending"
done_dir = "./wizard_data/done"
result_dir = "./data/pending"
result_pics_dir = "./data/pics"

header_re = "POST (STORY|FEEDS) \| (.+) \| @(13\.00|18\.00)"
tags_re = "(?:@)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)"

base_data = {
    "$schema": "../../schema.json",
}

# iterate over files in
# that directory
for folder_name in os.listdir(pending_dir):
    folder_dir = os.path.join(pending_dir, folder_name)
    if os.path.isdir(folder_dir):
        data_path = os.path.join(folder_dir, "data.txt")

        # Continue, parse data.txt
        if not os.path.isfile(data_path):
            continue
        datafile = open(data_path, "r", encoding="utf-8")
        post_info = datafile.readline().strip()
        user_tags = datafile.readline().strip()

        # Check post type
        post_info_data = re.match(header_re, post_info)
        user_tags_data = re.findall(tags_re, user_tags)

        assert post_info_data != None and user_tags_data != None

        # Attempt to parse date and time and convert into ISO8601
        date_str = post_info_data.group(2)
        time_str = post_info_data.group(3)

        proper_date_data = ddp.get_date_data(
            time_str + " " + date_str).date_obj.isoformat()

        target_files = [f for f in listdir(folder_dir) if isfile(
            join(folder_dir, f)) and f.endswith(".jpg")]
        target_files.sort()

        if len(target_files) == 0:
            raise Exception(f"No target .jpgs for {folder_name} ?")

        name_prefix = folder_name

        # Branch for Story and Feeds
        if post_info_data.group(1) == "STORY":
            generated_data = base_data.copy()
            generated_data["publish_datetime"] = proper_date_data
            generated_data["type"] = "STORY"
            generated_data["tags"] = user_tags_data

            # For each image inside the folder
            for idx, image_name in enumerate(target_files):
                per_image_data = generated_data.copy()

                image_path = join(folder_dir, image_name)
                new_image_path = join(
                    result_pics_dir, f"{name_prefix}-{idx}.jpg")
                new_json_path = join(
                    result_dir, f"{name_prefix}-{idx}.json")

                # Copy destination image to pics
                shutil.copy(image_path, new_image_path)

                # Create the JSON
                per_image_data["image_src"] = f"{name_prefix}-{idx}.jpg"

                # Dump the JSON
                with open(new_json_path, "w", encoding="utf-8") as outfile:
                    json.dump(per_image_data, outfile)

            datafile.close()
            # Move the entire folder to the done folder.
            shutil.move(folder_dir, done_dir)
        elif post_info_data.group(1) == "FEEDS":
            # For each image inside the folder
            generated_data = base_data.copy()
            generated_data["publish_datetime"] = proper_date_data
            generated_data["type"] = "FEED"
            generated_data["tags"] = user_tags_data

            # Get the caption
            datafile.readline()  # Eliminate --- trash
            generated_data["caption"] = datafile.read()

            if len(target_files) > 1:
                # Is an album
                # For each image inside the folder
                album_data = []
                for idx, image_name in enumerate(target_files):
                    per_image_data = generated_data.copy()

                    image_path = join(folder_dir, image_name)
                    new_image_path = join(
                        result_pics_dir, f"{name_prefix}-{idx}.jpg")

                    # Copy destination image to pics
                    shutil.copy(image_path, new_image_path)
                    album_data.append(f"{name_prefix}-{idx}.jpg")

                new_json_path = join(result_dir, f"{name_prefix}.json")
                generated_data["album"] = album_data

                # Dump the JSON
                with open(new_json_path, "w", encoding="utf-8") as outfile:
                    json.dump(generated_data, outfile)
            else:
                # Not an album
                image_path = join(folder_dir, target_files[0])
                new_image_path = join(result_pics_dir, f"{name_prefix}.jpg")
                generated_data["image_src"] = f"{name_prefix}.jpg"

                shutil.copy(image_path, new_image_path)

                new_json_path = join(result_dir, f"{name_prefix}.json")

                # Dump the JSON
                with open(new_json_path, "w", encoding="utf-8") as outfile:
                    json.dump(generated_data, outfile)

            datafile.close()
            # Move the entire folder to the done folder.
            shutil.move(folder_dir, done_dir)
        else:
            raise Exception("what type? STORY | FEEDS only allowed")
