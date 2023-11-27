#!/usr/bin/env python3
import json

# Function to process the JSON structure and convert it to the desired format
def process_json(input_data, output_data):
    if "Options" in input_data:
        options = input_data["Options"]
        formatted_options = {}
        for option in options:
            option_name = option["option"].strip(",")
            formatted_option = {
                "name": option_name,
                "help": option["description"]
            }
            formatted_options[option_name] = formatted_option
        output_data["options"] = formatted_options

    if "Commands" in input_data:
        for command, data in input_data["Commands"].items():
            subcommand_data = {
                "command": command,
                "args": [],
                "options": {},
                "subcommands": {}
            }

            if "description" in data:
                subcommand_data["help"] = data["description"]

            process_json(data, subcommand_data)

            output_data["subcommands"][command] = subcommand_data

# Load the JSON data from the input file
input_file = "goat_command_tree.json"
with open(input_file, "r") as f:
    input_data = json.load(f)

# Initialize the output data
output_data = {
    "goat": {
        "command": "goat",
        "args": [],
        "options": {},
        "subcommands": {}
    }
}

# Process the JSON data
process_json(input_data, output_data["goat"])

# Write the processed data to a new JSON file
output_file = "output.json"
with open(output_file, "w") as f:
    json.dump(output_data, f, indent=4)

print("Data has been saved to", output_file)
