#!/usr/bin/env python3
import subprocess
import re
import json
import copy

def add_command_key(data, parent_key=None):
    if isinstance(data, dict):
        keys_to_iterate = list(data.keys())
        subcommands_to_move = {}

        for key in keys_to_iterate:
            value = data[key]

            if isinstance(value, list) or isinstance(value, str):
                continue  # Skip lists and strings for now

            add_command_key(value, key)

            if key not in ('subcommands', 'options') and isinstance(value, dict):
                value['command'] = key

            if key == 'options':
                subcommands_to_move['options'] = copy.deepcopy(value)
                del data[key]

        if subcommands_to_move:
            data.update(subcommands_to_move)

        if 'subcommands' in data and not data['subcommands']:
            del data['subcommands']

def clean_output(output):
    """Remove special characters like bold and underline from the output."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)

def save_to_json(data, file_name="ibmcloud_command_tree.json"):
    """Save the command tree to a JSON file."""
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

def split_commands(command_string):
    """Split commands separated by a comma (,) into separate commands and choose one."""
    commands = [command.strip() for command in command_string.split(',')]
    # Choose the first command for simplicity
    return [commands[0]]

def get_ibmcloud_command_tree(prefix_command, parent_command=None, depth=0, max_depth=3):
    if depth > max_depth:
        return {}

    try:
        subcommands, flags = get_ibmcloud_subcommands_and_flags(prefix_command)
    except subprocess.CalledProcessError as e:
        print(f"Error while running '{prefix_command} --help': {e}")
        return {}

    command_parts = prefix_command.split()

    # Prepare the basic structure for this command/group
    command_info = {
        "depth": depth,
        "type": "group" if subcommands else "command",
        "options": flags,
        "command": command_parts[-1],
        "parent_command": parent_command,
        "help": get_ibmcloud_command_help(prefix_command)  # Capture command-level help
    }

    # If there are subcommands, explore them
    if subcommands:
        command_info["subcommands"] = {}
        for subcommand in subcommands:
            subcommand_names = split_commands(subcommand)
            for subcommand_name in subcommand_names:
                next_prefix_command = f"{prefix_command} {subcommand_name}"
                print(f"Exploring: {next_prefix_command}")
                subcommand_info = get_ibmcloud_command_tree(
                    next_prefix_command,
                    parent_command=command_info["command"],
                    depth=depth + 1,
                    max_depth=max_depth
                )
                if subcommand_info:
                    command_info["subcommands"][subcommand_name] = subcommand_info

        # Save the tree incrementally at each step
        try:
            if depth == 0:
                service = "ibmcloud"
            else:
                service = "ibmcloud_" + str(prefix_command.split(' ')[1])
        except IndexError:
            service = prefix_command
        save_to_json(command_info, file_name=f"{service}.json")

    return command_info

def get_ibmcloud_subcommands_and_flags(prefix_command):
    """Fetch the subcommands and flags for a given prefix_command."""
    complete_command = f"{prefix_command} --help"
    output = subprocess.check_output(complete_command, shell=True, text=True, stderr=subprocess.STDOUT)
    output = clean_output(output)

    lines = output.split("\n")
    subcommands = {}
    flags = {}
    in_subcommand_section = False
    collect_subcommands = False

    for line in lines:
        line = line.strip()

        if "COMMANDS:" in line:
            collect_subcommands = True
            continue
        if in_subcommand_section and not line:
            collect_subcommands = False
            continue
        if collect_subcommands and re.match(r'^[a-zA-Z0-9]', line):
            subcommand = line.split()[0]
            if not any(c.isupper() for c in subcommand):  # Skip commands with capital letters
                subcommands[subcommand] = {
                    "name": subcommand,
                    "help": "",
                    "flags": {}
                }

        if line.startswith('--'):
            flag, description = re.split(r'\s{2,}', line, maxsplit=1)
            flag = flag.strip()
            flags[flag] = {
                "name": flag,
                "help": description.split('.')[0].strip()  # Capture the first sentence as description
            }

    return subcommands, flags

def get_ibmcloud_command_help(prefix_command):
    """Fetch the help text for a given prefix_command."""
    complete_command = f"{prefix_command} --help"
    try:
        output = subprocess.check_output(complete_command, shell=True, text=True, stderr=subprocess.STDOUT)
        output = clean_output(output)
        help_text = ""
        help_section_started = False
        for line in output.split('\n'):
            line = line.strip()
            if help_section_started:
                if not line:  # Stop capturing after the first empty line
                    break
                help_text += line + ' '
            if line.startswith("NAME:"):
                help_section_started = True
        # Keep only the first sentence of the description
        first_sentence = help_text.split('.')[0] if '.' in help_text else help_text
        return first_sentence.strip()
    except subprocess.CalledProcessError as e:
        return ""

# Initial call to start building the command tree
root_command = "ibmcloud"
command_tree = get_ibmcloud_command_tree(root_command, parent_command=None, depth=0)

# Final save
save_to_json(command_tree)
