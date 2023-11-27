#!/usr/bin/env python3
from threading import Lock
import json
import re
import sys
import os
import click
import gnureadline
import subprocess
from time import sleep
from subprocess import Popen, PIPE, CalledProcessError
from pathlib import Path
import signal
import atexit

lock = Lock()
use_bold = True

def get_save_path(filename="oci.json"):
    user_home = Path.home()
    goat_shell_data_path = user_home / "goat" / "shell" / "data"
    goat_shell_data_path.mkdir(parents=True, exist_ok=True) # create directory if doesn't exist
    return goat_shell_data_path / filename

def interrupted(sig, frame):
    error_out("Interrupted")
    return

def bold(s=''):
    return '\033[1m' + s + '\033[0m' if use_bold else s

def error_out(msg):
    if msg.startswith('ServiceError:'):
        j = json.loads(msg[14:])
        print(bold('ServiceError(' + str(j['status']) + '): ' + str(j['code'])), file=sys.stderr)
        print(bold(j['message']), file=sys.stderr)
    else:
        print(bold(msg), file=sys.stderr)

def get_oci_commands(argv):
    def oci_command_out(cmd, eol=''):
        with lock:
            f.write(cmd + '\n')
        cmd = re.sub(r' [+-].*', '', cmd)
        print('\033[2K\r       ', cmd, end=eol, flush=True)

    def clean_up_param(s):
        param = re.sub(r' [A-Z[].*', '', s)
        type = s[len(param) + 1:]
        if type and not type.startswith('['):
            type = '[' + type.lower() + ']'
        longest_param = max(param.split(', '), key=len).strip()
        if longest_param != '--help':
            return longest_param + (' ' + type if type else '')

    oci_dir = os.path.expanduser('~/.oci')
    oci_commands_file = os.path.expanduser('oci_commands.txt')

    if len(sys.argv) == 2:
        sp = subprocess.run(['oci', '--help'], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        out = sp.stdout.decode('utf-8')
        part1 = re.sub(r'.*Options:\n|Commands:\n.*', '', out, flags=re.S)
        globals = sorted(list(dict.fromkeys(re.findall(r'(--[A-Za-z-]*[a-z])[, \n]', part1))))
        if not os.path.exists(oci_dir):
            os.mkdir(oci_dir, mode=0o755)
        print("Creating", bold(oci_commands_file))
        f = open(oci_commands_file, 'w')
        f.write('global_options ' + ' '.join(globals) + '\n')
        f.close()

        part2 = re.sub(r'.*Commands:\n', '', out, flags=re.S)
        services = sorted(list(dict.fromkeys(re.findall(r'^ {2,4}([a-z-]+)', part2, flags=re.MULTILINE))))
        processes = []
        for n, service in enumerate(services, start=1):
            print('\033[2K\r({}/{}) Getting {} commands...'.format(
                  n, len(services), service) + 30 * ' ')
            p = Popen([sys.argv[0], 'oci_commands', service])
            processes.append(p)

        # wait for all processes to finish
        for p in processes:
            p.wait()
        print('\033[2K\rDone.')
        return

    sp = subprocess.run(['oci'] + sys.argv[2:] + ['--help'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = sp.stdout.decode('utf-8')

    if out.startswith('Usage'):
        if re.search(r'\nCommands:\n', out, flags=re.M):
            commands = re.sub(r'.*\nCommands:\n', '', out, flags=re.S)
            for line in commands.splitlines():
                if re.match(r'^  [a-z0-9-]+', line):
                    cmd = line.strip().split(' ')[0]
                    subprocess.run([sys.argv[0], 'oci_commands'] + sys.argv[2:] + [cmd])
            print('\033[2K\r', end='')
            exit(0)

        m = re.search(r'Usage: (.*?) \[.*]', out, re.S)
        if m:
            cmd = re.sub(r'[ \n]+', ' ', m.group(1)).strip()
            print(cmd)
        param = ''
        required = []
        optional = []
        for ln in re.sub(r'.*\nOptions:\n', '', out, flags=re.S).splitlines():
            m = re.match(r'  (-.*?)(  |$)', ln)
            if m:
                if param:
                    optional.append(param)
                param = clean_up_param(m.group(1))
            if param and '[required]' in ln:
                required.append(param)
                param = ''
        if param:
            optional.append(param)

        if required:
            cmd += ' ' + ' '.join(sorted(required))
        if optional:
            cmd += ' + ' + ' '.join(sorted(optional))

        f = open(oci_commands_file, 'a')
        oci_command_out(cmd)
        f.close()
        exit(0)

    lines = re.sub(r'(\x08.|\x1B...)', '', out).splitlines()

    f = open(oci_commands_file, 'a')
    cmd = ''
    for n, line in enumerate(lines):
        if re.match('^(USAGE|   Usage)', line):
            if cmd:
                oci_command_out(cmd)
            cmd = re.sub(' .OPTIONS.', '', lines[n + 1]).strip()
            if not cmd:
                cmd = re.sub(' .OPTIONS.', '', lines[n + 2]).strip()

        elif re.search(r'^ {6,7}-[a-z0-9\-,]+($|.* \[.+])', line):
            cmd = cmd + ' ' + clean_up_param(line.strip())

        elif re.search(r'optional parameters', line, re.I):
            cmd = cmd + ' +'

        elif line.endswith('Accepted values are:'):
            s = re.sub(r', ', r'|', lines[n + 2].strip())
            cmd = cmd[:-5] + s + ']'

    oci_command_out(cmd, eol='\033[2K\r')
    f.close()
    exit(0)

def prompt_user_to_continue():
    """Prompts the user to decide if they want to continue the process."""
    print("INFO: this process will take approximately 3-4 hours to complete.")
    choice = input("INFO: do you want to continue? [yes/no]: ").strip().lower()

    if choice == "yes":
        return True
    elif choice == "no":
        return False
    else:
        print("INFO: invalid choice. Please enter 'yes' or 'no'.")
        return prompt_user_to_continue()  # Recursively ask until a valid choice is made.

def clean_argument(argument):
    return argument.strip("[]")

def parse_subcommands(lines):
    commands = {}
    global_options = {}
    for line in lines:
        parts = line.strip().split(" ")
        if len(parts) < 2:
            continue
        if parts[0] == 'global_options':
            global_options = parts[1:]
            continue
        main_command = parts[1]
        subcommand_chain = []

        for part in parts[2:]:
            if part.startswith("+") or part.startswith("--") or part.startswith("["):
                break
            subcommand_chain.append(part)

        if len(subcommand_chain) == 0:
            continue  # Skip lines with no subcommands

        current_command = commands.setdefault(main_command, {"subcommands": {}})
        current_subcommand = current_command["subcommands"]

        for subcommand in subcommand_chain:
            if subcommand not in current_subcommand:
                current_subcommand[subcommand] = {"command": subcommand, "subcommands": {}}
            current_subcommand = current_subcommand[subcommand]["subcommands"]

        last_subcommand = subcommand_chain[-1]
        if last_subcommand not in current_subcommand:
            current_subcommand[last_subcommand] = {"options": {}, "arguments": []}
        options = current_subcommand[last_subcommand]["options"]
        arguments = current_subcommand[last_subcommand]["arguments"]

        for part in parts[len(subcommand_chain) + 2:]:
            if part.startswith('--'):
                options[part] = {"name": part, "help": "N/A"}
            elif part.startswith('['):
                arguments.append(clean_argument(part))

        # Remove duplicates and sort arguments
        arguments = list(set(arguments))
        arguments.sort()

        current_subcommand[last_subcommand]["arguments"] = arguments

    return commands, global_options

def clean_output(text):
    # Remove backspace characters
    while '\x08' in text:
        idx = text.index('\x08')
        text = text[:idx-1] + text[idx+1:]
    return text

def get_description_from_help_text(help_text):
    lines = help_text.split('\n')
    capture = False
    description = []

    for line in lines:
        if 'DESCRIPTION' in line:
            capture = True
            continue  # Skip the line with 'DESCRIPTION' itself
        if 'USAGE' in line:
            capture = False  # Stop capturing at 'USAGE'

        if capture:
            description.append(line.strip())

    return ' '.join(description).strip()


def update_command_descriptions(command_tree, prefix_command=[]):
    if "subcommands" in command_tree:
        for subcommand, data in command_tree["subcommands"].items():
            full_command_list = prefix_command + [subcommand]
            full_command_str = " ".join(full_command_list)

            # Skip the command if it matches the parent command to avoid duplication
            if full_command_list[-1] == full_command_list[-2] if len(full_command_list) > 1 else False:
                continue

            # Print the command that will be executed
            print(f"EXECUTING {full_command_str} --help")

            try:
                output = subprocess.check_output(f"{full_command_str} --help", shell=True, text=True, stderr=subprocess.STDOUT)
                output = clean_output(output)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while running '{full_command_str} --help': {e}")
                continue

            description = get_description_from_help_text(output)
            if description:
                data["description"] = description
            else:
                print(f"Could not find description for {full_command_str}. Raw output:")

            update_command_descriptions(data, full_command_list)

def clean_subcommands(subcommands):
    keys_to_remove = []
    for key, value in subcommands.items():
        if 'subcommands' in value:
            nested_subcommands = value['subcommands']
            if key in nested_subcommands:
                # Found a redundant subcommand entry; schedule it for removal.
                keys_to_remove.append((nested_subcommands, key))
                # Copy the values from the redundant entry to the parent.
                for inner_key, inner_value in nested_subcommands[key].items():
                    if inner_key not in value:
                        value[inner_key] = inner_value
            # Recurse further to clean other subcommands
            clean_subcommands(nested_subcommands)
    # Actually remove the keys
    for dictionary, key in keys_to_remove:
        del dictionary[key]

if __name__ == "__main__":

    global_options_dict = {}
    if 'oci_commands' not in sys.argv:
        sys.argv = ['./get_oci_commands.py', 'oci_commands']

    get_oci_commands(sys.argv)

    # Read data from file or source
    with open('oci_commands.txt', 'r') as file:
        lines = file.readlines()
    command_tree, global_options = parse_subcommands(lines)
    for option in global_options:
        global_options_dict[option] = {
                "help": "This is a placeholder description for {}".format(option),
                "name": option
        }
    root_info = {
        "args": [],
        "command": "oci",
        "help": "Oracle Cloud Infrastructure command line interface, with support for Audit, Block Volume, Compute, Database, IAM, Load Balancing, Networking, DNS, File Storage, Email Delivery and Object Storage Services.",
        "options": global_options_dict,
        "subcommands": command_tree
    }
    command_tree = {"oci": root_info}
    
    # Save the output to a JSON file
    output_file = get_save_path("oci.json")

    # Update descriptions
    update_command_descriptions(command_tree["oci"], ["oci"])

    # clean up
    clean_subcommands(command_tree['oci']['subcommands'])

    # Save the updated JSON
    with open(output_file, "w") as f:
        json.dump(command_tree, f, sort_keys=True, indent=2)
