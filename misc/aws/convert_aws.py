#!/usr/bin/env python3
import json

def transform_subcommand(sub_data, command_name=None):
    transformed_subcommand = {
        "command": command_name,  # Add the "command" field
        "description": sub_data.get("description", ""),
        "options": {},
    }

    if "options" in sub_data:
        for option, option_data in sub_data["options"].items():
            transformed_subcommand["options"][option] = {"name": option, "help": option_data}

    if "commands" in sub_data:
        transformed_subcommand["subcommands"] = transform_data(sub_data["commands"])

    return transformed_subcommand

def transform_data(data):
    transformed_data = {}
    for cmd, cmd_data in data.items():
        transformed_data[cmd] = transform_subcommand(cmd_data, command_name=cmd)

    return transformed_data

# Load AWS JSON data
with open('aws_command_data.json', 'r') as f:
    aws_data = json.load(f)

# Check if "aws" and "subcommands" exist in the JSON data
if "aws" in aws_data and "subcommands" in aws_data["aws"]:
    # Transform the data
    transformed_data = transform_data(aws_data["aws"]["subcommands"])

    # Save the transformed data to a new JSON file
    with open('transformed_aws_command_data.json', 'w') as f:
        json.dump(transformed_data, f, indent=4)

    print("Data has been transformed and saved to transformed_aws_command_data.json.")
else:
    print("Invalid JSON structure. Please check your input JSON file.")

