#!/usr/bin/env python3
import subprocess
import json
import re
from pathlib import Path
import signal
import atexit

def get_save_path(filename="goat.json"):
    user_home = Path.home()
    goat_shell_data_path = user_home / "goat" / "shell" / "data"
    goat_shell_data_path.mkdir(parents=True, exist_ok=True) # create directory if doesn't exist
    return goat_shell_data_path / filename

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

        if current_section == "Commands":
            parts = line.split(None, 1)
            if len(parts) == 2:
                subcommand, description = parts
                parsed_data["Commands"][subcommand] = {"description": description.strip()}

    return parsed_data

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

def cleanup(filename="goat.json"):
    save_path = get_save_path(filename)
    if os.path.isfile(filename):
        os.remove(filename)

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 15 minutes to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

# Register cleanup function to handle the SIGINT (Ctrl_C) and SIGTERM signals
signal.signal(signal.SIGINT, lambda signum, frame: (cleanup(), sys.exit(1)))
signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup(), sys.exit(1)))

# Initialize data structure
initial_data = {"Options": [], "Commands": {}}

# Start processing top-level commands and save data per top-level command
recursive_parse("", initial_data)

# Save to a JSON file
with open("goat_command_tree.json", "w") as f:
    json.dump(initial_data, f, indent=4)

print("INFO: initial data has been saved to goat_command_tree.json")

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
output_file = get_save_path()
with open(output_file, "w") as f:
    json.dump(output_data, f, indent=4)

print("INFO: data has been saved to", output_file)
