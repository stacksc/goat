#!/usr/bin/env python3
from threading import Lock
import json
import re
import sys
import os
import subprocess
from time import sleep
from subprocess import Popen, PIPE, CalledProcessError

lock = Lock()
use_bold = True

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
    oci_commands_file = os.path.expanduser('~/.oci/oci_commands.txt')

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
        #exit(0)
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
            #return

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
    output_file = 'oci.json'
    with open(output_file, 'w') as json_file:
        json.dump(command_tree, json_file, indent=2)
    print(f"INFO: JSON saved to the following file: {output_file}")
