#!/usr/bin/env python3
import json
import os

# Directory containing your individual JSON files
json_directory = "../json"

# Dictionary to store the combined data
combined_data = {
    "az": {
        "command": "az",
        "args": [],
        "options": {},
        "subcommands": {},
        "help": "The Azure command-line interface (Azure CLI) is a set of commands used to create and manage Azure resources. The Azure CLI is available across Azure services and is designed to get you working quickly with Azure, with an emphasis on automation."
    }
}

# Function to fix the JSON structure
def fix_json_structure(data):
    if "command" in data and "subcommands" in data:
        # Check if there is a subcommand with the same name as the current command
        subcommand_name = data["command"]
        subcommand = data["subcommands"].get(subcommand_name)
        if subcommand:
            # Remove the redundant subcommand
            del data["subcommands"][subcommand_name]
            # Merge properties of the redundant subcommand into the current command
            data.update(subcommand)
    return data

# Iterate through each JSON file in the directory
for filename in os.listdir(json_directory):
    if filename.endswith(".json"):
        file_path = os.path.join(json_directory, filename)
        with open(file_path, "r") as file:
            try:
                data = json.load(file)
                # Fix the JSON structure
                data = fix_json_structure(data)
                command = data.get("command")
                if command:
                    combined_data["az"]["subcommands"][command] = data
            except json.JSONDecodeError as e:
                print(f"Skipping {filename} due to JSON decode error: {e}")

# Output file path for the combined JSON
output_file = "combined.json"

# Save the combined data to the output file
with open(output_file, "w") as outfile:
    json.dump(combined_data, outfile, indent=4)

print(f"Combined data saved to {output_file}")

