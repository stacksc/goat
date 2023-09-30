#!/usr/bin/env python3
import subprocess
import json
import re

# Function to get ovhai CLI help output for a specific command
def get_ovhai_help_output(command):
    try:
        if command:
            print(f"Fetching help with command: ovhai {command} -h")
            ovhai_help_output = subprocess.check_output(["ovhai"] + command.split() + ["-h"], text=True, stderr=subprocess.STDOUT)
        else:
            print("Fetching help for the top-level ovhai command")
            ovhai_help_output = subprocess.check_output(["ovhai", "-h"], text=True, stderr=subprocess.STDOUT)
        return ovhai_help_output
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while fetching ovhai CLI help: {str(e)}")
        return ""

# Function to extract subcommands and descriptions
def extract_subcommands_and_descriptions(ovhai_help_output):
    subcommands = {}
    options = {}
    subcommand_pattern = r'^\s*([a-z-]+)\s+(.*)$'
    option_pattern = r'^\s*(-[a-z-]+|--[a-z-]+(?:-[a-z-]+)*)\s+([^\n]*)$'

    is_options_section = False

    for line in ovhai_help_output.split('\n'):
        if line.strip().lower() == "options:":
            is_options_section = True
            continue

        if is_options_section:
            option_match = re.match(option_pattern, line)
            if option_match:
                option_name = option_match.group(1)
                option_description = option_match.group(2)
                # Check if the option name starts with a dash or two dashes before adding it
                if option_name.startswith('-'):
                    options[option_name] = {
                        "help": option_description.strip(),
                        "name": option_name
                    }
        else:
            match = re.match(subcommand_pattern, line)
            if match:
                subcommand_name = match.group(1)
                subcommand_description = match.group(2)
                subcommands[subcommand_name] = {
                    "args": [],
                    "command": subcommand_name,
                    "help": subcommand_description,
                    "options": {},
                    "subcommands": {}
                }

    return subcommands, options

# Function to build the CLI tree recursively
def build_cli_tree(command):
    ovhai_help_output = get_ovhai_help_output(command)

    subcommands, options = extract_subcommands_and_descriptions(ovhai_help_output)

    for subcommand in subcommands:
        subcommands[subcommand]["subcommands"], subcommands[subcommand]["options"] = build_cli_tree(f"{command} {subcommand}")

    return subcommands, options

# Main script
def main():
    # Recursively build the CLI tree starting from the top-level command
    top_level_dict = {
        "ovhai": {
            "args": [],
            "command": "ovhai",
            "options": {},
            "subcommands": {}
        }
    }

    top_level_dict["ovhai"]["subcommands"], top_level_dict["ovhai"]["options"] = build_cli_tree("")

    # Save the extracted data to a JSON file
    json_file = "ovhai_cli_data.json"
    with open(json_file, 'w') as f:
        json.dump(top_level_dict, f, indent=4)

if __name__ == "__main__":
    main()

