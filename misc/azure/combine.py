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

# Function to clean up description text
def clean_description(description):
    if ":" in description:
        _, cleaned_description = description.split(":", 1)
        # Split cleaned_description by newline characters and take the first part
        return cleaned_description.split('\n')[0].strip()
    return description.strip()

# Recursive function to process subcommands and clean "help" fields
def process_subcommands(data):
    if "subcommands" in data:
        for subcommand_name, subcommand_data in data["subcommands"].items():
            # Recursively process subcommands
            process_subcommands(subcommand_data)
            # Clean up the "help" field
            subcommand_data["help"] = clean_description(subcommand_data.get("help", ""))

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
                    # Clean up description field for top-level command
                    description = data.get("help", "")
                    data["help"] = clean_description(description)
                    # Recursively clean "help" fields for subcommands
                    process_subcommands(data)
                    combined_data["az"]["subcommands"][command] = data
            except json.JSONDecodeError as e:
                print(f"Skipping {filename} due to JSON decode error: {e}")

# Output file path for the combined JSON
output_file = "combined.json"

# Save the combined data to the output file
with open(output_file, "w") as outfile:
    json.dump(combined_data, outfile, indent=4)

print(f"Combined data saved to {output_file}")

