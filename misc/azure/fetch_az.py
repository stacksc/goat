#!/usr/bin/env python3
import subprocess
import re
import json
from pathlib import Path

def get_save_path(filename="az.json"):
    user_home = Path.home()
    goat_shell_data_path = user_home / "json"
    goat_shell_data_path.mkdir(parents=True, exist_ok=True) # create directory if it doesn't exist
    return goat_shell_data_path / filename

def listToStringWithoutBrackets(list1):
    return str(list1).replace('[','').replace(']','').replace("'", "").replace('{','').replace('}','')

# Set to track processed commands to avoid duplicates
processed_commands = set()

def get_top_level_commands():
    az_help_output = run_az_help("")
    top_level_commands = []

    # Initialize current_section
    current_section = None
    ignore_words = {'and', 'as', 'default', 'for', 'in', 'is', 'it', 'of', 'to', 'with', 'if', 'the'}

    # Parse the top-level commands from the help output
    for line in az_help_output.split("\n"):
        line = line.strip()

        if "Commands" in line:
            current_section = "commands"
        elif "Arguments" in line:
            current_section = "arguments"
        elif current_section == "commands" and line:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                subcommand, _ = parts
                subcommand = subcommand.strip()
                if " " not in subcommand and subcommand.islower() and subcommand not in ignore_words and not any(c in subcommand for c in "!@#$%^&*()[]{};:,.<>?/\\|~`'\""):
                    top_level_commands.append(subcommand)

    return top_level_commands

# Helper function to clean up command-line output
def clean_output(output):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)

# Function to run 'az' command and fetch its help info
def run_az_help(command):
    try:
        print(f"Running: az {command} -h")
        output = subprocess.check_output(['az'] + command.split() + ['-h'], stderr=subprocess.STDOUT, text=True)
        return clean_output(output)
    except subprocess.CalledProcessError as e:
        print(f"Error running az {command} -h")
        return ""

# Function to parse the 'az' help output and extract subcommands and options
def parse_az_help(output):
    parsed_data = {"args": [], "options": {}, "subcommands": {}, "arguments": {}}
    current_section = None
    option_description = ""
    command_description = ""

    if output == "":
        return parsed_data

    for line in output.split("\n"):
        line = line.strip()
        if '--cmd' in line:
            continue
        if "Subgroups" in line or "Commands" in line:
            current_section = "subcommands"
        elif "Arguments" in line:
            current_section = "arguments"
        elif "Global Arguments" in line:
            current_section = "global_arguments"
        elif current_section is None:
            # Capture the description for the top-level command
            command_description += line

        if current_section in ["arguments", "global_arguments"]:
            if line.startswith("--"):
                # New option found, save the previous option description
                if option_description:
                    option_parts = option_description.split(":", 1)
                    if len(option_parts) == 2:
                        option_name = option_parts[0].strip().split()[0]  # Take the first part as the option name
                        option_description = option_parts[1].strip()
                        if option_name.startswith("--"):
                            parsed_data["options"][option_name] = {"help": option_description}
                option_description = line
            else:
                # Append to the existing option description
                option_description += " " + line

        if current_section == "subcommands":
            parts = line.split(" ", 1)
            if len(parts) == 2:
                subcommand, description = parts
                subcommand = subcommand.strip()
                description = listToStringWithoutBrackets(description.split(':')[-1:]).strip()

                # Check if the subcommand name consists of valid characters
                if re.match(r'^[a-zA-Z0-9_-]+$', subcommand) and not subcommand[0].isupper() and "To" not in subcommand:
                    # Skip subcommands with common words in the description
                    common_words = {'and', 'as', 'default', 'for', 'in', 'is', 'it', 'of', 'to', 'with', 'if', 'the'}
                    words = description.split()
                    if not any(word in common_words for word in words):
                        parsed_data["subcommands"][subcommand] = {"help": description, "command": subcommand, "args": [], "options": {}, "subcommands": {}}

    # Handle the last option description
    if option_description and option_description.startswith("--"):
        option_parts = option_description.split(":", 1)
        if len(option_parts) == 2:
            option_name = option_parts[0].strip().split()[0]  # Take the first part as the option name
            option_description = option_parts[1].strip()
            if option_name.startswith("--"):
                parsed_data["options"][option_name] = {"help": option_description}

    # Use the captured command description as the "help" field
    parsed_data["help"] = command_description
    return parsed_data

def recursive_parse(command, parent_data, stop_condition=None):
    subcommands_to_remove = []
    if command in processed_commands:
        return

    processed_commands.add(command)
    output = run_az_help(command)

    if not output:
        # Skip processing if the command returned an error
        return

    parsed_data = parse_az_help(output)

    current_data = parent_data
    if command:
        last_part = command.split()[-1]
        current_data = parent_data["subcommands"].setdefault(last_part, {"command": last_part, "args": [], "options": {}, "subcommands": {}})

    if stop_condition and stop_condition in parsed_data["options"]:
        return
    if '--cmd' in parsed_data["options"]:
        return

    current_data.update(parsed_data)
    for subcommand in parsed_data["subcommands"].keys():
        new_command = f"{command} {subcommand}".strip()
        recursive_parse(new_command, current_data, stop_condition)

top_level_commands = get_top_level_commands()

for top_level_command in top_level_commands:
    initial_data = {"command": top_level_command, "args": [], "options": {}, "subcommands": {}}
    recursive_parse(top_level_command, initial_data, stop_condition="--cmd")

    # Save the entire top-level command data including its description
    json_file = get_save_path(f"az_{top_level_command}.json")
    with open(json_file, "w") as f:
        json.dump(initial_data, f, indent=4)
    print(f"Data for {top_level_command} saved.")

print("Data has been saved to individual JSON files for each top-level command.")

