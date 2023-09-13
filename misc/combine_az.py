#!/usr/bin/env python3
import os
import json

# Create an empty dictionary to store the combined command tree
combined_command_tree = {
    "az": {
        "command": "az",
        "args": [],
        "options": {},
        "subcommands": {},
        "help": "The Azure command-line interface (Azure CLI) is a set of commands used to create and manage Azure resources. The Azure CLI is available across Azure services and is designed to get you working quickly with Azure, with an emphasis on automation."
    }
}

# Directory where JSON files are stored
json_files_directory = "./json"

# Iterate over the JSON files
for filename in os.listdir(json_files_directory):
    if filename.endswith(".json"):
        with open(os.path.join(json_files_directory, filename), "r") as json_file:
            data = json.load(json_file)

            # Merge the loaded dictionary with the combined command tree
            combined_command_tree["az"]["subcommands"].update({data["command"]: data})

# Save the combined command tree to a single JSON file
with open("combined_command_tree.json", "w") as output_file:
    json.dump(combined_command_tree, output_file, indent=4)

print("Combined command tree has been saved to combined_command_tree.json")

