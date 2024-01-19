#!/usr/bin/env python3
import click, os, json, re, sys, subprocess, copy
from toolbox.logger import Log
from toolbox.misc import set_terminal_width, get_save_path
import signal
import atexit
from pathlib import Path

@click.group('extract', invoke_without_command=True, help='extract the command tree for IBM CLI', context_settings={'help_option_names':['-h','--help'], 'max_content_width': set_terminal_width()})
@click.pass_context
def extract(ctx):
    pass

@extract.command(help='manually refresh the IBM CLI command tree', context_settings={'help_option_names':['-h','--help']})
@click.pass_context
def commands(ctx):

    json_file = get_save_path("ibmcloud.json")

    # Register cleanup function to handle the SIGINT (Ctrl_C) and SIGTERM signals
    signal.signal(signal.SIGINT, lambda signum, frame: (cleanup(), sys.exit(1)))
    signal.signal(signal.SIGTERM, lambda signum, frame: (cleanup(), sys.exit(1)))

    if not prompt_user_to_continue():
        print("INFO: exiting the script now...")
        exit()

    # Initial call to start building the command tree
    root_command = "ibmcloud"
    command_tree = get_ibmcloud_command_tree(root_command, parent_command=None, depth=0, max_depth=3)

    # Create the root "ibmcloud" key and add the command_tree as a subcommand
    command_tree = {root_command: command_tree}

    # Final save
    save_to_json(command_tree, json_file)

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 1 hour to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

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

def save_to_json(data, file_name="ibmcloud.json"):
    """Save the command tree to a JSON file."""
    with open(file_name, "w") as f:
        json.dump(data, f, sort_keys=True, indent=2)

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

