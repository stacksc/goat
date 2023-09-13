#!/usr/bin/env python3
import subprocess
import re
import json

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
    ignore_words = ['and', 'as', 'default', 'for', 'in', 'is', 'it', 'of', 'to', 'with', 'if', 'the', 'be', 'end', 'all']
    last = command.split(" ")[-1:]
    pattern = ','.join(last)
    if pattern in ignore_words:
        print(f"INFO: skipping running az {command} -h")
        return ""
    try:
        print(f"Running: az {command} -h")
        output = subprocess.check_output(['az'] + command.split() + ['-h'], stderr=subprocess.STDOUT, text=True)
        return clean_output(output)
    except subprocess.CalledProcessError as e:
        print(f"Error running az {command} -h")
        return ""

# Function to parse the 'az' help output and extract subcommands and options
def parse_az_help(output):
    parsed_data = {"args": [], "options": {}, "subcommands": {}}
    current_section = None
    option_description = ""

    for line in output.split("\n"):
        line = line.strip()
        if '--cmd' in line:
            continue
        if "Subgroups" in line or "Commands" in line:
            current_section = "subcommands"
        elif "Arguments" in line:
            current_section = "arguments"

        if current_section == "subcommands":
            parts = line.split(" ", 1)
            if len(parts) == 2:
                subcommand, description = parts
                subcommand = subcommand.strip()

                # Check if the subcommand name consists of valid characters
                if re.match(r'^[a-zA-Z0-9_-]+$', subcommand) and not subcommand[0].isupper() and "To" not in subcommand:
                    parsed_data["subcommands"][subcommand] = {"command": subcommand, "args": [], "options": {}, "subcommands": {}}
        elif current_section == "arguments":
            if line.startswith("--"):
                option_parts = line.split(":", 1)
                if len(option_parts) == 2:
                    option, option_description = option_parts
                    option = option.split()[0].strip()  # Extract only the first word
                    option_description = option_description.strip()
                    parsed_data["options"][option] = {"name": option, "help": option_description}
                else:
                    option_description = ""

    return parsed_data

# Recursive function to traverse the command tree
def recursive_parse(command, parent_data, stop_condition=None):
    if command in processed_commands:
        return

    processed_commands.add(command)
    output = run_az_help(command)
    parsed_data = parse_az_help(output)

    current_data = parent_data
    if command:
        last_part = command.split()[-1]
        current_data = parent_data["subcommands"].setdefault(last_part, {"command": last_part, "args": [], "options": {}, "subcommands": {}})

    current_data.update(parsed_data)

    if stop_condition and stop_condition in parsed_data["options"]:
        return
    if '--cmd' in parsed_data["options"]:
        return

    # Recursively process subcommands
    for subcommand in parsed_data["subcommands"].keys():
        new_command = f"{command} {subcommand}".strip()
        recursive_parse(new_command, current_data, stop_condition)

# Start processing top-level commands and save data per top-level command
top_level_commands = get_top_level_commands()

for top_level_command in top_level_commands:
    initial_data = {"command": "", "args": [], "options": {}, "subcommands": {}}
    recursive_parse(top_level_command, initial_data, stop_condition="--cmd")
    with open(f"az_command_tree_{top_level_command}.json", "w") as f:
        json.dump(initial_data["subcommands"][top_level_command], f, indent=4)
    print(f"Data for {top_level_command} saved.")

print("Data has been saved to individual JSON files for each top-level command.")
