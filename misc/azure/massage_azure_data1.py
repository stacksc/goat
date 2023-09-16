#!/usr/bin/env python3
import json

# Load data from the first JSON file
with open('az_command_tree.json', 'r') as file1:
    data1 = json.load(file1)

# Extract descriptions from the first JSON file
descriptions = {key: entry.get('description', '') for key, entry in data1.items()}

# Load data from the second JSON file
with open('az.json', 'r') as file2:
    data2 = json.load(file2)

# Update the second JSON data with descriptions
def add_help_field(command_data):
    if 'command' in command_data:
        command_key = command_data['command']
        if command_key in descriptions:
            command_data['help'] = descriptions[command_key]

# Recursively traverse the data2 JSON and add 'help' fields
def traverse_and_add_help(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                add_help_field(value)
                traverse_and_add_help(value)
            elif isinstance(value, list):
                for item in value:
                    traverse_and_add_help(item)
            else:
                add_help_field(data)

# Start traversal
traverse_and_add_help(data2)

# Save the updated data to a new JSON file
with open('az_updated.json', 'w') as updated_file:
    json.dump(data2, updated_file, indent=4)

