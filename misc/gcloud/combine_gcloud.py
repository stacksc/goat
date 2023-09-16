#!/usr/bin/env python3
import os
import json

def clean_key(key):
    """Remove commas and periods from the given key."""
    return key.replace(',', '').replace('.', '')

def clean_dict_keys(data):
    """Recursively clean keys in a nested dictionary."""
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = clean_key(key)
            if isinstance(value, dict):
                new_data[new_key] = clean_dict_keys(value)
            elif isinstance(value, list):
                new_data[new_key] = [clean_dict_keys(item) if isinstance(item, dict) else item for item in value]
            else:
                new_data[new_key] = value
        return new_data
    elif isinstance(data, list):
        return [clean_dict_keys(item) if isinstance(item, dict) else item for item in data]
    else:
        return data

# Create an empty dictionary to store the combined command tree
combined_command_tree = {
    "gcloud": {
        "command": "gcloud",
        "args": [],
        "options": {},
        "subcommands": {},
        "help": "The gcloud CLI manages authentication, local configuration, developer workflow, and interactions with the Google Cloud APIs."
    }
}

# Directory where JSON files are stored
json_files_directory = "./gcloud"

# Iterate over the JSON files
for filename in os.listdir(json_files_directory):
    if filename.endswith(".json"):
        with open(os.path.join(json_files_directory, filename), "r") as json_file:
            data = json.load(json_file)

            # Clean up the data
            cleaned_data = clean_dict_keys(data)

            # Merge the loaded dictionary with the combined command tree
            combined_command_tree["gcloud"]["subcommands"].update({cleaned_data["command"]: cleaned_data})

# Save the combined command tree to a single JSON file
with open("combined_command_tree.json", "w") as output_file:
    json.dump(combined_command_tree, output_file, sort_keys=True, indent=4)

print("Combined command tree has been saved to combined_command_tree.json")
