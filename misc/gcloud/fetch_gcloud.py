#!/usr/bin/env python3
import subprocess
import re
import json
import copy

def get_description_from_help_text(help_text):
    lines = help_text.split('\n')
    found_description = False
    description_buffer = ""
    
    for i, line in enumerate(lines):
        if "DESCRIPTION" in line:
            found_description = True
            continue  # Skip the line containing "DESCRIPTION"
        
        if found_description:
            if line.strip():  # continue reading the description if the line is not empty
                description_buffer += " " + line.strip()
            else:  # stop reading at the first empty line after finding "DESCRIPTION"
                return description_buffer.strip()
    
    return None

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

def save_to_json(data, file_name="gcloud_command_tree.json"):
    """Save the command tree to a JSON file."""
    with open("./gcloud/" + file_name, "w") as f:
        json.dump(data, f, indent=4)

def get_gcloud_command_tree(prefix_command, parent_command=None, depth=0, max_depth=3):
    """Recursively build the gcloud command tree."""
    if depth > max_depth:
        return {}

    subcommands, flags, description = get_gcloud_subcommands_and_flags(prefix_command)
    command_parts = prefix_command.split()

    # Prepare the basic structure for this command/group
    command_info = {
        "depth": depth,
        "type": "group" if subcommands else "command",
        "options": flags,
        "command": command_parts[-1],
        "parent_command": parent_command,
        "help": description  # Added description here
    }

    # If there are subcommands, explore them
    if subcommands:
        command_info["subcommands"] = {}
        for subcommand in subcommands:
            next_prefix_command = f"{prefix_command} {subcommand}"
            print(f"Exploring: {next_prefix_command}")
            command_info["subcommands"][subcommand] = get_gcloud_command_tree(
                next_prefix_command,
                parent_command=command_info["command"],
                depth=depth + 1,
                max_depth=max_depth
            )

        # Save the tree incrementally at each step
        try:
            service = "gcloud_" + str(prefix_command.split(' ')[1])
        except IndexError:
            service = prefix_command
        save_to_json(command_info, file_name=f"{service}.json")

    return command_info

def get_gcloud_subcommands_and_flags(prefix_command):
    """Fetch the subcommands and flags for a given prefix_command."""
    complete_command = f"{prefix_command} --help"
    try:
        output = subprocess.check_output(complete_command, shell=True, text=True, stderr=subprocess.STDOUT)
        output = clean_output(output)
    except subprocess.CalledProcessError as e:
        print(f"Error while running '{complete_command}': {e}")
        return None, None, None

    lines = output.split("\n")
    subcommands = {}
    flags = {}
    in_subcommand_section = False
    collect_subcommands = False
    description = ''
    description = get_description_from_help_text(output)
    description_buffer = ''
    reading_description = False

    for line in lines:
        line = line.strip()

        if "GROUP is one of the following:" in line or "COMMAND is one of the following:" in line:
            collect_subcommands = True
            continue
        if in_subcommand_section and not line:
            collect_subcommands = False
            continue

        if reading_description:
            if line:  # continue reading the description if line is not empty
                description_buffer += " " + line
            else:  # end of description
                flags[flag]["help"] = description_buffer.strip()
                reading_description = False
                continue

        if collect_subcommands and re.match(r'^[a-zA-Z0-9]', line):
            subcommand = line.split()[0].strip('.')
            if not any(c.isupper() for c in subcommand):  # Skip commands with capital letters
                subcommands[subcommand] = {
                    "name": subcommand,
                    "help": "",
                    "flags": {}
                }

        if line.startswith('--'):
            flag = line.split()[0]
            description_buffer = line[len(flag):].strip()
            flags[flag] = {
                "name": flag,
                "help": description_buffer
            }
            reading_description = True

    return subcommands, flags, description

# Initial call to start building the command tree
root_command = "gcloud"
command_tree = {
    "gcloud": {
        "args": [],
        "command": "gcloud",
        "help": "",
        "options": [],
        "subcommands": get_gcloud_command_tree(root_command)
    }
}

# Final save
save_to_json(command_tree)
