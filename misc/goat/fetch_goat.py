#!/usr/bin/env python3
import subprocess
import json
import re

# Function to run 'goat' command and fetch its help info
def run_goat_help(command):
    try:
        print(f"Running: goat {command} -h")
        output = subprocess.check_output(['goat'] + command.split() + ['-h'], stderr=subprocess.STDOUT, text=True)
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error running goat {command} -h")
        return ""

# Function to parse the 'goat' help output and extract subcommands and options
def parse_goat_help(output):
    parsed_data = {"Options": [], "Commands": {}}
    current_section = None
    lines = output.split("\n")
    options = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "Options:" in line:
            current_section = "Options"
            continue
        elif "Commands:" in line:
            current_section = "Commands"
            continue

        if current_section == "Options":
            # Use regular expression to match and extract options
            option_match = re.match(r'(-[a-zA-Z0-9,]+|--[a-zA-Z0-9,]+)\s+([^\n]*)', line)
            if option_match:
                option, description = option_match.groups()
                options[option] = description.strip()

        parsed_data["Options"] = options
        print(parsed_data["Options"])

        if current_section == "Commands":
            parts = line.split(None, 1)
            if len(parts) == 2:
                subcommand, description = parts
                parsed_data["Commands"][subcommand] = {"description": description.strip()}

    return parsed_data

# Recursive function to traverse the command tree
# Recursive function to traverse the command tree
def recursive_parse(command, parent_data):
    output = run_goat_help(command)
    parsed_data = parse_goat_help(output)

    if "Commands" not in parent_data:
        parent_data["Commands"] = {}

    parent_data["Commands"].update(parsed_data["Commands"])

    # Extract option descriptions
    option_descriptions = {}

    # Update descriptions based on patterns
    for line in output.splitlines():
        line = line.strip()
        if line and line[0] in ('-', '--'):
            parts = line.split(None, 1)
            if len(parts) == 2:
                option, description = parts
                option_descriptions[option] = description.strip()

    # Add option descriptions to parent data
    if "Options" not in parent_data:
        parent_data["Options"] = []

    # Append option descriptions as dictionaries
    for option, description in option_descriptions.items():
        parent_data["Options"].append({"option": option, "description": description})

    for subcommand in parsed_data["Commands"].keys():
        new_command = f"{command} {subcommand}".strip()
        print(f"Subcommand: {new_command}")
        parsed_data["Commands"][subcommand] = recursive_parse(new_command, parsed_data["Commands"][subcommand])

    return parsed_data


# Initialize data structure
initial_data = {"Options": [], "Commands": {}}

# Start processing top-level commands and save data per top-level command
recursive_parse("", initial_data)

# Save to a JSON file
with open("goat_command_tree.json", "w") as f:
    json.dump(initial_data, f, indent=4)

print("Data has been saved to goat_command_tree.json")
